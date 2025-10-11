from datetime import date

from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, field_validator, HttpUrl

from validation import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)

class ProfileCreateSchema(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    gender: str = Field(..., example="man")
    date_of_birth: date = Field(..., example="1990-01-01")
    info: str = Field(..., example="This is a test profile.")
    avatar: UploadFile

    @validator("first_name")
    def validate_first_name(cls, value):
        return validate_name(value)

    @validator("last_name")
    def validate_last_name(cls, value):
        return validate_name(value)

    @validator("gender")
    def validate_gender_field(cls, value):
        return validate_gender(value)

    @validator("date_of_birth")
    def validate_birth(cls, value):
        return validate_birth_date(value)

    @validator("info")
    def validate_info(cls, value):
        if not value.strip():
            raise ValueError("Info cannot be empty or whitespace.")
        return value

class ProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: str

