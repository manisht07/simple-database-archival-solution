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

import oracledb


def create_dsn(hostname: str, port: str, service: str) -> str:
    """Create an Oracle DSN that works across versions using service name."""
    return oracledb.makedsn(hostname, port, service_name=service)

def convert_schema(column_type: str) -> str:
    """Map Oracle data types to Glue types."""

    t = column_type.upper()

    if "CHAR" in t or "CLOB" in t or "LONG" in t or "VARCHAR" in t:
        return "string"
    elif "RAW" in t or "BLOB" in t or "BFILE" in t:
        return "binary"
    elif "FLOAT" in t:
        return "float"
    elif "INT" in t or "INTEGER" in t:
        return "int"
    elif "NUMBER" in t or "DEC" in t:
        return "decimal"
    elif "TIMESTAMP" in t or "DATE" in t:
        return "timestamp"
    else:
        return "string"


class Connection:
    def __init__(self, hostname, port, username, password, database, oracle_owner):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.oracle_owner = oracle_owner

    def get_schema(self):
        
        table_list = []
        
        try:

            oracle_tables = []
            dsn = create_dsn(self.hostname, self.port, self.database)
            with oracledb.connect(user=self.username, password=self.password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    sql = f"""SELECT owner, table_name  FROM all_tables WHERE OWNER = '{self.oracle_owner}'"""
                    for r in cursor.execute(sql):
                        oracle_tables.append(r[1])
            
            for table in oracle_tables:
                row_list = []
                cnn = oracledb.connect(user=self.username, password=self.password,
                                    dsn=dsn)
                cursor = cnn.cursor()
                
                cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS WHERE TABLE_NAME=\'" + table + "\'and OWNER=\'" + self.oracle_owner + "\'")
                schema_list = cursor.fetchall()
                print(table)
                for schema in schema_list:
                    row_type = convert_schema(schema[1])
                    print(schema[1])
                    row_list.append(
                        {"key": schema[0], "value": row_type, "existing": True})

                cursor.close()
                table_list.append(
                    {"table": table, "schema": row_list})
                print(table_list)
            return table_list

        except Exception:
            return False
