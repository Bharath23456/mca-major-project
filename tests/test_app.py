from fastapi.testclient import TestClient
from app.main import app
from app.db import Database
from app.llm import LLM

client = TestClient(app)


def test_query_list_users():
    r = client.post('/query', json={'prompt': 'List users'})
    assert r.status_code == 200
    j = r.json()
    assert 'clarify' in j


def test_sample_data_is_expanded_and_repeatable():
    db = Database(':memory:')
    db.schema_text()
    initial_users = db.execute('SELECT COUNT(*) AS count FROM users')[0]['count']
    initial_orders = db.execute('SELECT COUNT(*) AS count FROM orders')[0]['count']

    db._ensure_sample()

    assert initial_users == 10
    assert initial_orders == 11
    assert db.execute('SELECT COUNT(*) AS count FROM users')[0]['count'] == initial_users
    assert db.execute('SELECT COUNT(*) AS count FROM orders')[0]['count'] == initial_orders


def test_database_supports_postgresql_url():
    db = Database('postgresql://user:pass@localhost:5432/appdb')
    assert db.dialect == 'postgresql'


def test_database_supports_sql_server_url():
    db = Database('mssql://user:pass@localhost:1433/appdb?driver=ODBC+Driver+17+for+SQL+Server')
    assert db.dialect == 'sqlserver'


def test_llm_tracks_database_dialect():
    llm = LLM('postgresql')
    assert llm.dialect == 'postgresql'

    llm_sqlserver = LLM('sqlserver')
    assert llm_sqlserver.dialect == 'sqlserver'
