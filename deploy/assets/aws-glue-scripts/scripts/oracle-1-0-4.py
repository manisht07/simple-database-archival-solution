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

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame


def directJDBCSource(
    glueContext,
    connectionName,
    connectionType,
    database,
    table,
    redshiftTmpDir,
    transformation_ctx,
) -> DynamicFrame:

    connection_options = {
        "useConnectionProperties": "true",
        "dbtable": table,
        "connectionName": connectionName,
    }

    if redshiftTmpDir:
        connection_options["redshiftTmpDir"] = redshiftTmpDir

    return glueContext.create_dynamic_frame.from_options(
        connection_type=connectionType,
        connection_options=connection_options,
        transformation_ctx=transformation_ctx,
    )


args = getResolvedOptions(sys.argv, ["JOB_NAME", "TABLE", "BUCKET", "DATABASE", "ARCHIVE_ID", "MAPPINGS", "OWNER", "CONNECTION"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

print(args)
print(args["OWNER"] + "." + args["TABLE"])
print("s3://" + args["BUCKET"] + "/" + args["ARCHIVE_ID"] + "/" + args["DATABASE"] + "/" + args["TABLE"] + "/")

# Script generated for node Oracle table
OracleSQLtable_node1 = directJDBCSource(
    glueContext,
    connectionName=args["CONNECTION"],
    connectionType="oracle",
    database=args["DATABASE"],
    table=args["OWNER"] + "." + args["TABLE"],
    redshiftTmpDir="",
    transformation_ctx="OracleSQLtable_node1",
)

tuples = list(map(tuple, json.loads(args["MAPPINGS"])))

# Script generated for node ApplyMapping
ApplyMapping_node2 = ApplyMapping.apply(
    frame=OracleSQLtable_node1,
    mappings=tuples,
    transformation_ctx="ApplyMapping_node2",
)

# Script generated for node S3 bucket
S3bucket_node3 = glueContext.write_dynamic_frame.from_options(
    frame=ApplyMapping_node2,
    connection_type="s3",
    format="glueparquet",
        connection_options={
        "path": "s3://" + args["BUCKET"] + "/" + args["ARCHIVE_ID"] + "/" + args["DATABASE"] + "/" + args["TABLE"] + "/",
        "partitionKeys": [],
    },
    transformation_ctx="S3bucket_node3",
    format_options={"compression": "uncompressed"},
)

job.commit()
