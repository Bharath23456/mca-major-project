from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.llm import LLM
from app.clarifier import Clarifier
from app.db import Database
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# serve static demo
app.mount("/static", StaticFiles(directory="./static"), name="static")

db = Database()
llm = LLM(db.dialect)
clarifier = Clarifier(llm)


@app.get("/")
async def frontend():
    return FileResponse("./static/index.html")


class ClarifyRequest(BaseModel):
    original_prompt: str
    answer: str


class QueryRequest(BaseModel):
    prompt: str


@app.post("/query")
async def query(req: QueryRequest):
    schema_text = db.schema_text()
    sql, need_clarify, clarification = await llm.text_to_sql(req.prompt, schema=schema_text)

    if need_clarify:
        return {"clarify": True, "question": clarification}

    try:
        rows = db.execute(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"clarify": False, "sql": sql, "rows": rows}


@app.post("/clarify")
async def clarify(req: ClarifyRequest):
    schema_text = db.schema_text()
    sql, need_clarify, question = await clarifier.handle_clarification(req.original_prompt, req.answer, schema=schema_text)
    if need_clarify:
        return {"clarify": True, "question": question}

    try:
        rows = db.execute(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"clarify": False, "sql": sql, "rows": rows}
