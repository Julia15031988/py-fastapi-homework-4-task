from pydantic import BaseModel, HttpUrl, field_validator, ConfigDict
from datetime import date
from validation import (
    validate_name,
    validate_gender,
    validate_birth_date,
    validate_image,
)
from fastapi import Form, UploadFile, File, HTTPException, APIRouter, Form, Depends, HTTPException, Request, status


class ProfileCreateRequestSchema(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: UploadFile | None

    @classmethod
    def from_form(
            cls,
            first_name: str = Form(...),
            last_name: str = Form(...),
            gender: str = Form(...),
            date_of_birth: date = Form(...),
            info: str = Form(...),
            avatar: UploadFile = File(...),
    ) -> "ProfileCreateRequestSchema":
        stripped_info = info.strip()
        if not stripped_info:
            # вручну піднімаємо помилку, щоб не падало в Pydantic
            raise ValueError("Info must not be empty.")
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=stripped_info,
            avatar=avatar,
        )

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        validate_name(value)
        return value.strip().lower()

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str) -> str:
        validate_name(value)
        return value.strip().lower()

    @field_validator("gender")
    @classmethod
    def validate_gender_field(cls, value: str) -> str:
        validate_gender(value)
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth(cls, value: date) -> date:
        validate_birth_date(value)
        return value

    @field_validator("info")
    @classmethod
    def validate_info(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Info must not be empty.")
        return value.strip()

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, value: UploadFile) -> UploadFile:
        try:
            validate_image(value)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{
                    "type": "value_error",
                    "loc": ["avatar"],
                    "msg": str(e),
                    "input": value.filename,
                }],
            )
        return value


class ProfileCreateResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: HttpUrl
