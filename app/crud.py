from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Plan, User
from .schemas import UserInput


def save_user(
    db: Session,
    data: UserInput
) -> User:

    existing = db.scalar(
        select(User).where(
            User.user_id == data.user_id
        )
    )

    if existing:

        existing.name = data.name
        existing.age = data.age
        existing.weight = data.weight
        existing.goal = data.goal
        existing.intensity = data.intensity

        db.commit()
        db.refresh(existing)

        return existing

    user = User(
        **data.model_dump()
    )

    db.add(user)

    db.commit()
    db.refresh(user)

    return user


def save_plan(
    db: Session,
    user_id: str,
    original_plan: str,
    nutrition_tip: str
) -> Plan:

    plan = Plan(
        user_id=user_id,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )

    db.add(plan)

    db.commit()
    db.refresh(plan)

    return plan


def get_user(
    db: Session,
    user_id: str
) -> User | None:

    return db.scalar(
        select(User).where(
            User.user_id == user_id
        )
    )


def get_latest_plan(
    db: Session,
    user_id: str
) -> Plan | None:

    return db.scalar(
        select(Plan)
        .where(Plan.user_id == user_id)
        .order_by(Plan.created_at.desc())
    )


def update_plan(
    db: Session,
    plan: Plan,
    updated_plan: str,
    feedback: str
) -> Plan:

    plan.updated_plan = updated_plan

    plan.feedback = feedback

    plan.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(plan)

    return plan


def get_all_users_with_plans(
    db: Session
):

    users = db.scalars(
        select(User)
        .order_by(User.created_at.desc())
    ).all()

    result = []

    for user in users:

        plans = db.scalars(
            select(Plan)
            .where(
                Plan.user_id == user.user_id
            )
            .order_by(
                Plan.created_at.desc()
            )
        ).all()

        result.append(
            (user, plans)
        )

    return result