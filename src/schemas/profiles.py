from pydantic import BaseModel, HttpUrl, field_validator, ConfigDict
from datetime import date
from validation import (
    validate_name,
    validate_gender,
    validate_birth_date,
)


class ProfileCreateRequestSchema(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, value: str) -> str:
        return validate_name(value)

    @field_validator("last_name")
    @classmethod
    def validate_last_name(cls, value: str) -> str:
        return validate_name(value)

    @field_validator("gender")
    @classmethod
    def validate_gender_field(cls, value: str) -> str:
        return validate_gender(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth(cls, value: date) -> date:
        return validate_birth_date(value)

    @field_validator("info")
    @classmethod
    def validate_info(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Info must not be empty.")
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
