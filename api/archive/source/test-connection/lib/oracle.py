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


class Connection:
    def __init__(self, hostname, port, username, password, database, oracle_owner):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.oracle_owner = oracle_owner

    def testConnection(self):

        try:

            dsn = create_dsn(self.hostname, self.port, self.database)
            with oracledb.connect(user=self.username, password=self.password, dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    sql = """SELECT owner, table_name  FROM all_tables WHERE OWNER = 'DMS_SAMPLE'"""
                    for r in cursor.execute(sql):
                        print(r)

            # cursor.close()

            return True

        except Exception as e:
            print(e)
            return False
