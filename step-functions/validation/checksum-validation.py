"""
Lambda to validate table checksums by comparing row counts
from the source database and the archived table stored in S3.
"""

import boto3
import json
import logging
import os
import time
import traceback

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger()
if logger.hasHandlers():
    logger.setLevel(LOG_LEVEL)
else:
    logging.basicConfig(level=LOG_LEVEL)

ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
secrets = boto3.client('secretsmanager')
athena = boto3.client('athena')
sqs = boto3.client('sqs')


def mask_sensitive_data(event):
    keys_to_redact = ["authorization"]
    result = {}
    for k, v in event.items():
        if isinstance(v, dict):
            result[k] = mask_sensitive_data(v)
        elif k in keys_to_redact:
            result[k] = "<redacted>"
        else:
            result[k] = v
    return result


def build_response(http_code, body):
    return {
        "headers": {
            "Cache-Control": "no-cache, no-store",
            "Content-Type": "application/json",
        },
        "statusCode": http_code,
        "body": body,
    }


def get_source_count(engine, host, port, user, password, database, table, owner=""):
    try:
        if engine == "mysql":
            import pymysql
            conn = pymysql.connect(host=host, user=user, password=password, database=database)
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                result = cur.fetchone()[0]
            conn.close()
            return int(result)
        if engine == "mssql":
            import pymssql
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                result = cur.fetchone()[0]
            conn.close()
            return int(result)
        if engine == "oracle":
            import oracledb
            dsn = oracledb.makedsn(host, port, service_name=database)
            with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {owner}.{table}")
                    result = cur.fetchone()[0]
            return int(result)
    except Exception:  # pragma: no cover - best effort connection
        logger.error(traceback.format_exc())
        return None


def get_s3_count(archive_id, database, table, bucket):
    query = (
        f'SELECT COUNT(*) FROM "{archive_id}-{database}-database".'
        f'"{archive_id}-{database}-{table}-table"'
    )
    response = athena.start_query_execution(
        QueryString=query,
        ResultConfiguration={"OutputLocation": f's3://{bucket}/queries/'}
    )
    query_id = response["QueryExecutionId"]
    state = "RUNNING"
    while state == "RUNNING":
        time.sleep(2)
        res = athena.get_query_execution(QueryExecutionId=query_id)
        state = res["QueryExecution"]["Status"]["State"]
    if state != "SUCCEEDED":
        return None
    result = athena.get_query_results(QueryExecutionId=query_id)
    return int(result["ResultSet"]["Rows"][1]["Data"][0]["VarCharValue"])


def lambda_handler(event, context):
    logger.info(mask_sensitive_data(event))
    try:
        body = json.loads(event["body"]) if "body" in event else event
        archive_id = body["archive_id"]

        table_param = ssm.get_parameter(Name="/archive/dynamodb-table", WithDecryption=True)
        table = dynamodb.Table(table_param["Parameter"]["Value"])
        archive = table.get_item(Key={"id": archive_id})["Item"]

        secret = secrets.get_secret_value(SecretId=archive["secret_arn"])
        password = secret["SecretString"]

        queue_param = ssm.get_parameter(Name="/sqs/validation", WithDecryption=True)
        queue_url = queue_param["Parameter"]["Value"]
        bucket_param = ssm.get_parameter(Name="/athena/s3-athena-temp-bucket", WithDecryption=True)
        bucket = bucket_param["Parameter"]["Value"]

        for idx, tbl in enumerate(archive["table_details"]):
            source = get_source_count(
                archive["database_engine"],
                archive["hostname"],
                archive["port"],
                archive["username"],
                password,
                archive["database"],
                tbl["table"],
                archive.get("oracle_owner", ""),
            )
            s3_count = get_s3_count(archive_id, archive["database"], tbl["table"], bucket)
            match = source == s3_count
            table.update_item(
                Key={"id": archive_id},
                UpdateExpression=f'set table_details[{idx}].checksum_validation = :v',
                ExpressionAttributeValues={
                    ":v": {
                        "state": "COMPLETED",
                        "source_count": source,
                        "s3_count": s3_count,
                        "match": match,
                    }
                },
            )
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({"archive_id": archive_id, "checksum_complete": True}),
            )
        return build_response(200, json.dumps({"status": "Checksum validation complete"}))
    except Exception:
        logger.error(traceback.format_exc())
        return build_response(500, "Server Error")
