"""
Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.

Licensed under the Amazon Software License (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at

  http://aws.amazon.com/asl/

or in the "license" file accompanying this file. This file is distributed
on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing
permissions and limitations under the License.
"""

import boto3
import json
import logging
import os
import traceback

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ssm = boto3.client('ssm')

# region Logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger()

if logger.hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr.
    # If a handler is already configured, `.basicConfig` does not execute,
    # so we set the level directly.
    logger.setLevel(LOG_LEVEL)
else:
    logging.basicConfig(level=LOG_LEVEL)

# endregion


def mask_sensitive_data(event):
    # remove sensitive data from request object before logging
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
            # tell cloudfront and api gateway not to cache the response
            "Cache-Control": "no-cache, no-store",
            "Content-Type": "application/json",
        },
        "statusCode": http_code,
        "body": body,
    }


def lambda_handler(event, context):
    logger.info(mask_sensitive_data(event))

    try:

        body = json.loads(
            event["body"]) if "body" in event else json.loads(event)
        archive_id = body["archive_id"]
        legal_hold = body["legal_hold"]

        bucket_parameter = ssm.get_parameter(
            Name='/job/s3-bucket-table-data', WithDecryption=True)

        bucket_name = bucket_parameter['Parameter']['Value']

        parameter = ssm.get_parameter(
            Name='/archive/dynamodb-table', WithDecryption=True)
        table = dynamodb.Table(parameter['Parameter']['Value'])

        bucket = s3.Bucket(bucket_name)

        try:
            for object_summary in bucket.objects.filter(Prefix=archive_id):
                s3_client.put_object_legal_hold(
                    Bucket=bucket_name,
                    Key=object_summary.key,
                    LegalHold={
                        'Status': legal_hold
                    },
                )

            if legal_hold == 'ON':
                table.update_item(
                    Key={'id': archive_id},
                    UpdateExpression="SET legal_hold= :s",
                    ExpressionAttributeValues={':s': True},
                    ReturnValues="UPDATED_NEW"
                )
            elif legal_hold == 'OFF':
                table.update_item(
                    Key={'id': archive_id},
                    UpdateExpression="SET legal_hold= :s",
                    ExpressionAttributeValues={':s': False},
                    ReturnValues="UPDATED_NEW"
                )
        except Exception:
            logger.error(traceback.format_exc())
            return build_response(500, "Server Error")

        response = {"legal_hold": legal_hold}
        return build_response(200, json.dumps(response))
    except Exception:
        logger.error(traceback.format_exc())
        return build_response(500, "Server Error")


if __name__ == "__main__":

    example_event = {}
    response = lambda_handler(example_event, {})
    print(json.dumps(response))
