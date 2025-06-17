import oracledb


def create_dsn(hostname: str, port: str, service: str) -> str:
    return oracledb.makedsn(hostname, port, service_name=service)


class Connection:
    def __init__(self, hostname, port, username, password, database):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database

    def list_schemas(self):
        dsn = create_dsn(self.hostname, self.port, self.database)
        with oracledb.connect(user=self.username, password=self.password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT USERNAME FROM ALL_USERS")
                return [row[0] for row in cursor.fetchall()]
