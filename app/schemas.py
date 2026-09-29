from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


Goal = Literal[
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
    "endurance",
]


Intensity = Literal[
    "low",
    "medium",
    "high",
]


Experience = Literal[
    "beginner",
    "intermediate",
    "advanced",
]


class UserInput(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    user_id: str = Field(
        min_length=2,
        max_length=80,
    )

    age: int = Field(
        ge=13,
        le=100,
    )

    weight: float = Field(
        gt=20,
        le=300,
    )

    goal: Goal

    intensity: Intensity

    experience_level: Experience = "beginner"

    @field_validator(
        "name",
        "user_id",
    )
    @classmethod
    def clean_text(cls, value: str) -> str:

        return " ".join(
            value.strip().split()
        )


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=80,
    )

    feedback: str = Field(
        min_length=3,
        max_length=1000,
    )


class GenerateResponse(BaseModel):

    user_id: str

    workout_plan: str

    nutrition_tip: str

    ai_enabled: bool


class FeedbackResponse(BaseModel):

    user_id: str

    updated_plan: str

    nutrition_tip: str

    ai_enabled: bool