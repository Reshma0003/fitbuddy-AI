from pydantic import BaseModel, Field, field_validator


GOALS = {
    "weight loss",
    "muscle gain",
    "general wellness",
    "flexibility",
}


INTENSITIES = {
    "low",
    "medium",
    "high",
}


class UserInput(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    user_id: str = Field(
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$"
    )

    age: int = Field(
        ge=18,
        le=100
    )

    weight: float = Field(
        ge=25,
        le=300
    )

    goal: str

    intensity: str

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:

        value = value.strip().lower()

        if value not in GOALS:
            raise ValueError(
                f"Goal must be one of: {', '.join(sorted(GOALS))}"
            )

        return value

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: str) -> str:

        value = value.strip().lower()

        if value not in INTENSITIES:
            raise ValueError(
                "Intensity must be low, medium, or high"
            )

        return value


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=50
    )

    feedback: str = Field(
        min_length=3,
        max_length=1000
    )