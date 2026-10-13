from datetime import date
from typing import Optional
 
from pydantic import BaseModel, Field, model_validator
 
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
 
 
class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    email: Optional[str] = Field(None, pattern=EMAIL_PATTERN)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9\- ]{7,15}$")
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
 
 
class StudentCreate(StudentBase):
    @model_validator(mode="after")
    def need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least one of: email, phone")
        return self
 
 
class StudentUpdate(BaseModel):
    """All fields optional - used for PATCH (partial update)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[str] = Field(None, pattern=EMAIL_PATTERN)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9\- ]{7,15}$")
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
 
 
class Student(StudentBase):
    id: int