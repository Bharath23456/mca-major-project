# GenAI Text-to-SQL (workspace copy)

Demo FastAPI app that converts natural language to SQL with a clarification step.

Run locally:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/

The default database is SQLite. You can also point the app at MySQL, PostgreSQL, or SQL Server by setting `DATABASE` in `.env`.

Examples:
- SQLite: `sqlite:///./data/sample.db`
- MySQL: `mysql+pymysql://root:password@127.0.0.1:3306/text_to_sql`
- PostgreSQL: `postgresql://postgres:password@127.0.0.1:5432/text_to_sql`
- SQL Server: `mssql://sa:password@127.0.0.1:1433/text_to_sql?driver={ODBC+Driver+17+for+SQL+Server}`

The target database must already exist before starting the backend, except for SQLite where the file will be created automatically.
