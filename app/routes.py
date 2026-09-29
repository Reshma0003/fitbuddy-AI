from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import HTMLResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy import select

from sqlalchemy.orm import (
    Session,
    joinedload,
)

from .config import settings

from .database import get_db

from .gemini_service import (
    generate_nutrition_tip_with_flash,
    generate_workout_gemini,
    update_workout_plan,
)

from .models import (
    Plan,
    User,
)

from .schemas import (
    FeedbackRequest,
    GenerateResponse,
    UserInput,
)


router = APIRouter()


templates = Jinja2Templates(
    directory="templates"
)


def get_user(
    db: Session,
    user_id: str,
):

    user = db.scalar(
        select(User)
        .options(
            joinedload(User.plan)
        )
        .where(
            User.user_id == user_id
        )
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User ID not found.",
        )

    return user


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "settings": settings,
            "error": None,
        },
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse,
)
def generate_workout_form(

    request: Request,

    name: str = Form(...),

    user_id: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

    experience_level: str = Form(
        "beginner"
    ),

    db: Session = Depends(get_db),
):

    try:

        data = UserInput(
            name=name,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
            experience_level=experience_level,
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "settings": settings,
                "error": str(exc),
            },
            status_code=422,
        )

    user = db.scalar(
        select(User).where(
            User.user_id == data.user_id
        )
    )

    if user is None:

        user = User(
            **data.model_dump()
        )

        db.add(user)

        db.flush()

    else:

        for key, value in data.model_dump().items():

            setattr(
                user,
                key,
                value,
            )

    workout_plan, workout_ai = (
        generate_workout_gemini(user)
    )

    nutrition_tip, nutrition_ai = (
        generate_nutrition_tip_with_flash(
            user.goal
        )
    )

    if user.plan:

        user.plan.original_plan = workout_plan

        user.plan.updated_plan = None

        user.plan.feedback = None

        user.plan.nutrition_tip = nutrition_tip

        user.plan.updated_nutrition_tip = None

    else:

        user.plan = Plan(
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )

    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "settings": settings,
            "user": user,
            "plan": user.plan,
            "ai_enabled": (
                workout_ai and nutrition_ai
            ),
            "message": None,
        },
    )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse,
)
def submit_feedback_form(

    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    payload = FeedbackRequest(
        user_id=user_id,
        feedback=feedback,
    )

    user = get_user(
        db,
        payload.user_id,
    )

    if not user.plan:

        raise HTTPException(
            status_code=404,
            detail="No workout plan exists.",
        )

    base_plan = (
        user.plan.updated_plan
        or user.plan.original_plan
    )

    revised_plan, workout_ai = (
        update_workout_plan(
            user,
            base_plan,
            payload.feedback,
        )
    )

    revised_tip, nutrition_ai = (
        generate_nutrition_tip_with_flash(
            user.goal
        )
    )

    user.plan.updated_plan = revised_plan

    user.plan.updated_nutrition_tip = (
        revised_tip
    )

    user.plan.feedback = (
        payload.feedback
    )

    user.plan.updated_at = (
        datetime.now(timezone.utc)
    )

    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "settings": settings,
            "user": user,
            "plan": user.plan,
            "ai_enabled": (
                workout_ai and nutrition_ai
            ),
            "message": (
                "Your plan has been updated successfully."
            ),
        },
    )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse,
)
def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):

    users = db.scalars(
        select(User)
        .options(
            joinedload(User.plan)
        )
        .order_by(
            User.created_at.desc()
        )
    ).unique().all()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "request": request,
            "settings": settings,
            "users": users,
        },
    )


@router.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "FitBuddy",
    }


@router.post(
    "/api/generate-workout",
    response_model=GenerateResponse,
)
def api_generate_workout(
    payload: UserInput,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.user_id == payload.user_id
        )
    )

    if user is None:

        user = User(
            **payload.model_dump()
        )

        db.add(user)

        db.flush()

    else:

        for key, value in payload.model_dump().items():

            setattr(
                user,
                key,
                value,
            )

    workout, workout_ai = (
        generate_workout_gemini(user)
    )

    tip, nutrition_ai = (
        generate_nutrition_tip_with_flash(
            user.goal
        )
    )

    if user.plan:

        user.plan.original_plan = workout

        user.plan.updated_plan = None

        user.plan.feedback = None

        user.plan.nutrition_tip = tip

        user.plan.updated_nutrition_tip = None

    else:

        user.plan = Plan(
            original_plan=workout,
            nutrition_tip=tip,
        )

    db.commit()

    return GenerateResponse(
        user_id=user.user_id,
        workout_plan=workout,
        nutrition_tip=tip,
        ai_enabled=(
            workout_ai and nutrition_ai
        ),
    )


@router.post(
    "/api/users/{user_id}/feedback",
)
def api_feedback(
    user_id: str,
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):

    user = get_user(
        db,
        user_id,
    )

    if not user.plan:

        raise HTTPException(
            status_code=404,
            detail="No plan found.",
        )

    revised, workout_ai = (
        update_workout_plan(
            user,
            user.plan.updated_plan
            or user.plan.original_plan,
            feedback,
        )
    )

    tip, nutrition_ai = (
        generate_nutrition_tip_with_flash(
            user.goal
        )
    )

    user.plan.updated_plan = revised

    user.plan.updated_nutrition_tip = tip

    user.plan.feedback = feedback

    user.plan.updated_at = (
        datetime.now(timezone.utc)
    )

    db.commit()

    return {
        "user_id": user_id,
        "updated_plan": revised,
        "nutrition_tip": tip,
        "ai_enabled": (
            workout_ai and nutrition_ai
        ),
    }


@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db),
):

    users = db.scalars(
        select(User)
        .options(
            joinedload(User.plan)
        )
        .order_by(
            User.created_at.desc()
        )
    ).unique().all()

    return [
        {
            "user_id": user.user_id,
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "experience_level":
                user.experience_level,
            "created_at":
                user.created_at.isoformat()
                if user.created_at
                else None,
            "has_updated_plan":
                bool(
                    user.plan
                    and user.plan.updated_plan
                ),
        }
        for user in users
    ]