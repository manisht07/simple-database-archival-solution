import json
import logging
import os
import traceback
from lib import oracle

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger()
if logger.hasHandlers():
    logger.setLevel(LOG_LEVEL)
else:
    logging.basicConfig(level=LOG_LEVEL)

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

def build_response(code, body):
    return {
        "headers": {
            "Cache-Control": "no-cache, no-store",
            "Content-Type": "application/json",
        },
        "statusCode": code,
        "body": body,
    }

def lambda_handler(event, context):
    logger.info(mask_sensitive_data(event))
    body = json.loads(event.get("body", "{}"))

    hostname = body.get("hostname")
    port = body.get("port")
    username = body.get("username")
    password = body.get("password")
    database = body.get("database")
    engine = body.get("database_engine")

    if engine != "oracle":
        return build_response(400, json.dumps({"error": "Unsupported engine"}))
    try:
        conn = oracle.Connection(hostname, port, username, password, database)
        schemas = conn.list_schemas()
        return build_response(200, json.dumps({"schemas": schemas}))
    except Exception:
        logger.error(traceback.format_exc())
        return build_response(500, "Server Error")
