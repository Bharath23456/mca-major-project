import os
import sqlite3
from urllib.parse import urlparse, parse_qs

import pymysql
from dotenv import load_dotenv

try:
    import psycopg2
except Exception:
    psycopg2 = None

try:
    import pyodbc
except Exception:
    pyodbc = None

load_dotenv()

DATABASE = os.getenv("DATABASE", "./data/sample.db")


def detect_database_type(database_url: str) -> str:
    value = (database_url or "").lower()
    if value.startswith(("postgres://", "postgresql://", "postgresql+psycopg2://")):
        return "postgresql"
    if value.startswith(("mysql://", "mysql+pymysql://")):
        return "mysql"
    if value.startswith(("mssql://", "mssql+pyodbc://", "sqlserver://", "sqlserver+pyodbc://")):
        return "sqlserver"
    if value.startswith("sqlite"):
        return "sqlite"
    if value.endswith(".db") or value.startswith("./") or value.startswith("data/"):
        return "sqlite"
    return "sqlite"


class Database:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or DATABASE
        self.dialect = detect_database_type(self.database_url)
        self.conn = None

    def _connect(self):
        if self.conn is not None:
            return self.conn

        if self.dialect == "mysql":
            parsed = urlparse(self.database_url.replace("mysql+pymysql://", "mysql://", 1))
            if not parsed.hostname or not parsed.path.strip("/"):
                raise ValueError("DATABASE must include MySQL host and database name")
            self.conn = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username or "root",
                password=parsed.password or "",
                database=parsed.path.lstrip("/"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.Cursor,
            )
        elif self.dialect == "postgresql":
            if psycopg2 is None:
                raise ImportError("psycopg2 is required for PostgreSQL support. Install it with pip install psycopg2-binary")
            parsed = urlparse(self.database_url)
            if not parsed.hostname or not parsed.path.strip("/"):
                raise ValueError("DATABASE must include PostgreSQL host and database name")
            self.conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username or "postgres",
                password=parsed.password or "",
                dbname=parsed.path.lstrip("/"),
            )
        elif self.dialect == "sqlserver":
            if pyodbc is None:
                raise ImportError("pyodbc is required for SQL Server support. Install it with pip install pyodbc")
            parsed = urlparse(self.database_url)
            if not parsed.hostname or not parsed.path.strip("/"):
                raise ValueError("DATABASE must include SQL Server host and database name")
            params = parse_qs(parsed.query)
            driver = params.get("driver", ["{ODBC Driver 17 for SQL Server}"])[0]
            self.conn = pyodbc.connect(
                "DRIVER=" + driver + ";"
                + f"SERVER={parsed.hostname};"
                + f"PORT={parsed.port or 1433};"
                + f"DATABASE={parsed.path.lstrip('/')};"
                + f"UID={parsed.username or ''};"
                + f"PWD={parsed.password or ''};"
            )
        else:
            db_path = self.database_url
            if db_path.startswith("sqlite:///"):
                db_path = db_path.replace("sqlite:///", "", 1)
            elif db_path.startswith("sqlite://"):
                db_path = db_path.replace("sqlite://", "", 1)
            if db_path in ("", ":memory:"):
                db_path = ":memory:"
            elif not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            directory = os.path.dirname(db_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

        self._ensure_sample()
        return self.conn

    def _ensure_sample(self):
        cur = self.conn.cursor()
        if self.dialect == "postgresql":
            cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT, age INTEGER);")
            cur.execute("CREATE TABLE IF NOT EXISTS orders (id SERIAL PRIMARY KEY, user_id INTEGER, total REAL);")
            cur.execute("INSERT INTO users (name, age) SELECT 'Alice', 30 WHERE NOT EXISTS (SELECT 1 FROM users WHERE name='Alice');")
            cur.execute("INSERT INTO users (name, age) SELECT 'Bob', 25 WHERE NOT EXISTS (SELECT 1 FROM users WHERE name='Bob');")
            cur.execute("INSERT INTO orders (user_id, total) SELECT 1, 99.9 WHERE NOT EXISTS (SELECT 1 FROM orders WHERE user_id=1);")
        elif self.dialect == "sqlserver":
            cur.execute("IF OBJECT_ID('users', 'U') IS NULL CREATE TABLE users (id INT IDENTITY(1,1) PRIMARY KEY, name NVARCHAR(255), age INT);")
            cur.execute("IF OBJECT_ID('orders', 'U') IS NULL CREATE TABLE orders (id INT IDENTITY(1,1) PRIMARY KEY, user_id INT, total FLOAT);")
            cur.execute("IF NOT EXISTS (SELECT 1 FROM users WHERE name = 'Alice') INSERT INTO users (name, age) VALUES ('Alice', 30);")
            cur.execute("IF NOT EXISTS (SELECT 1 FROM users WHERE name = 'Bob') INSERT INTO users (name, age) VALUES ('Bob', 25);")
            cur.execute("IF NOT EXISTS (SELECT 1 FROM orders WHERE user_id = 1) INSERT INTO orders (user_id, total) VALUES (1, 99.9);")
        else:
            cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);")
            cur.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL);")
            cur.execute("INSERT INTO users (name, age) SELECT 'Alice', 30 WHERE NOT EXISTS (SELECT 1 FROM users WHERE name='Alice');")
            cur.execute("INSERT INTO users (name, age) SELECT 'Bob', 25 WHERE NOT EXISTS (SELECT 1 FROM users WHERE name='Bob');")
            cur.execute("INSERT INTO orders (user_id, total) SELECT 1, 99.9 WHERE NOT EXISTS (SELECT 1 FROM orders WHERE user_id=1);")
        placeholder = "?" if self.dialect in ("sqlite", "sqlserver") else "%s"
        users = [
            ("Charlie", 34),
            ("Diana", 28),
            ("Evan", 42),
            ("Fatima", 31),
            ("Grace", 24),
            ("Henry", 37),
            ("Isabella", 29),
            ("Jamal", 45),
        ]
        for name, age in users:
            cur.execute(
                f"INSERT INTO users (name, age) SELECT {placeholder}, {placeholder} "
                f"WHERE NOT EXISTS (SELECT 1 FROM users WHERE name={placeholder});",
                (name, age, name),
            )

        orders = [
            ("Alice", 149.50),
            ("Bob", 75.25),
            ("Charlie", 210.00),
            ("Diana", 48.75),
            ("Evan", 320.40),
            ("Fatima", 89.99),
            ("Grace", 135.00),
            ("Henry", 62.50),
            ("Isabella", 175.25),
            ("Jamal", 245.00),
        ]
        for name, total in orders:
            cur.execute(
                f"INSERT INTO orders (user_id, total) "
                f"SELECT (SELECT id FROM users WHERE name={placeholder}), {placeholder} "
                f"WHERE NOT EXISTS (SELECT 1 FROM orders "
                f"WHERE user_id=(SELECT id FROM users WHERE name={placeholder}) "
                f"AND total={placeholder});",
                (name, total, name, total),
            )
        self.conn.commit()

    def schema_text(self):
        conn = self._connect()
        cur = conn.cursor()
        if self.dialect == "mysql":
            cur.execute("SHOW TABLES")
            tables = [row[0] for row in cur.fetchall()]
            definitions = []
            for table in tables:
                cur.execute(f"SHOW CREATE TABLE `{table}`")
                definitions.append(f"{table}: {cur.fetchone()[1]}")
            return "\n".join(definitions)

        if self.dialect == "postgresql":
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
            tables = [row[0] for row in cur.fetchall()]
            definitions = []
            for table in tables:
                cur.execute(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position;",
                    (table,),
                )
                columns = ", ".join(f"{name} {dtype}{' NULL' if nullable == 'YES' else ' NOT NULL'}" for name, dtype, nullable in cur.fetchall())
                definitions.append(f"{table}: ({columns})")
            return "\n".join(definitions)

        if self.dialect == "sqlserver":
            cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;")
            tables = [row[0] for row in cur.fetchall()]
            definitions = []
            for table in tables:
                cur.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION;",
                    (table,),
                )
                columns = ", ".join(f"{name} {dtype}{' NULL' if nullable == 'YES' else ' NOT NULL'}" for name, dtype, nullable in cur.fetchall())
                definitions.append(f"{table}: ({columns})")
            return "\n".join(definitions)

        rows = conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table';").fetchall()
        return "\n".join([f"{row[0]}: {row[1]}" for row in rows])

    def execute(self, sql: str):
        low = sql.strip().lower()
        if not low.startswith("select"):
            raise ValueError("Only SELECT queries are allowed in demo mode.")
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return rows
