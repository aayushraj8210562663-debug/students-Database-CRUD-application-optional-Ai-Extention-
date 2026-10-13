import os
import re
import sqlite3
 
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
 
from database import DB_PATH, SCHEMA
 
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
 
router = APIRouter(prefix="/ai", tags=["AI (optional)"])
 
 
class Question(BaseModel):
    question: str
 
 
def _ollama(prompt: str) -> str:
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["response"].strip()
    except httpx.HTTPError as e:
        raise HTTPException(503, f"Ollama not reachable at {OLLAMA_URL}: {e}")
 
 
def _clean_sql(text: str) -> str:
    text = re.sub(r"```(?:sql)?", "", text).strip().rstrip(";").strip()
    # Safety: exactly one statement, SELECT only, no write keywords.
    if ";" in text or not re.match(r"(?is)^select\b", text):
        raise HTTPException(400, f"Model did not return a single SELECT: {text!r}")
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|create|attach|pragma|replace)\b", text):
        raise HTTPException(400, "Generated query contained a forbidden keyword")
    return text
 
 
@router.post("/ask")
def ask(body: Question):
    sql = _clean_sql(_ollama(
        f"SQLite schema:\n{SCHEMA}\n"
        "Write ONE SQLite SELECT query that answers the question. "
        "Return only the SQL, no explanation.\n"
        f"Question: {body.question}"
    ))
 
    # Read-only connection: even a bad query cannot modify data.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute(sql).fetchmany(50)]
    except sqlite3.Error as e:
        raise HTTPException(400, f"Generated SQL failed: {e} | SQL: {sql}")
    finally:
        conn.close()
 
    answer = _ollama(
        f"Question: {body.question}\nSQL result rows (JSON): {rows}\n"
        "Answer the question briefly in plain English using only these rows."
    )
    return {"question": body.question, "sql": sql, "rows": rows, "answer": answer}
 