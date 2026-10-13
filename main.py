import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional
 
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
 
from ai_extension import router as ai_router
from database import get_conn, init_db
from schemas import Student, StudentCreate, StudentUpdate
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
 
 
app = FastAPI(title="Students Database API", version="1.0.0", lifespan=lifespan)
app.include_router(ai_router)
 
COLUMNS = "id, name, date_of_birth, email, phone, course, address, enrollment_date"
 
 
def _get_or_404(conn: sqlite3.Connection, student_id: int) -> dict:
    row = conn.execute(f"SELECT {COLUMNS} FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Student {student_id} not found")
    return dict(row)
 
 
def _write(conn: sqlite3.Connection, sql: str, params: tuple):
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur
    except sqlite3.IntegrityError:
        raise HTTPException(409, "A student with this email already exists")
 
 
def _to_params(data: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}
 
 
# ---------- CREATE ----------
@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, conn: sqlite3.Connection = Depends(get_conn)):
    d = _to_params(student.model_dump())
    cur = _write(
        conn,
        "INSERT INTO students (name, date_of_birth, email, phone, course, address, enrollment_date) "
        "VALUES (:name, :date_of_birth, :email, :phone, :course, :address, :enrollment_date)",
        d,
    )
    return _get_or_404(conn, cur.lastrowid)
 
 
# ---------- READ (list / filter) ----------
@app.get("/students", response_model=List[Student])
def list_students(
    name: Optional[str] = Query(None, description="Substring match"),
    course: Optional[str] = Query(None, description="Exact match (case-insensitive)"),
    email: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    conn: sqlite3.Connection = Depends(get_conn),
):
    where, params = [], []
    if name:
        where.append("name LIKE ?"); params.append(f"%{name}%")
    if course:
        where.append("LOWER(course) = LOWER(?)"); params.append(course)
    if email:
        where.append("email = ?"); params.append(email)
    sql = f"SELECT {COLUMNS} FROM students"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    return [dict(r) for r in conn.execute(sql, (*params, limit, skip)).fetchall()]
 
 
# ---------- READ (single) ----------
@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    return _get_or_404(conn, student_id)
 
 
# ---------- UPDATE ----------
@app.put("/students/{student_id}", response_model=Student)
def replace_student(student_id: int, student: StudentCreate, conn: sqlite3.Connection = Depends(get_conn)):
    _get_or_404(conn, student_id)
    d = _to_params(student.model_dump()); d["id"] = student_id
    _write(
        conn,
        "UPDATE students SET name=:name, date_of_birth=:date_of_birth, email=:email, phone=:phone, "
        "course=:course, address=:address, enrollment_date=:enrollment_date WHERE id=:id",
        d,
    )
    return _get_or_404(conn, student_id)
 
 
@app.patch("/students/{student_id}", response_model=Student)
def update_student(student_id: int, changes: StudentUpdate, conn: sqlite3.Connection = Depends(get_conn)):
    _get_or_404(conn, student_id)
    d = _to_params(changes.model_dump(exclude_unset=True))
    if not d:
        raise HTTPException(400, "No fields to update")
    sets = ", ".join(f"{k} = ?" for k in d)  # keys come from the schema, not the client
    _write(conn, f"UPDATE students SET {sets} WHERE id = ?", (*d.values(), student_id))
    return _get_or_404(conn, student_id)
 
 
# ---------- DELETE ----------
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    _get_or_404(conn, student_id)
    _write(conn, "DELETE FROM students WHERE id = ?", (student_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
 