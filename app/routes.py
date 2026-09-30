from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from .config import get_settings

from .crud import (
    get_all_users_with_plans,
    get_latest_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)

from .database import get_db

from .gemini_service import (
    GeminiServiceError,
    generate_nutrition_tip_with_flash,
    generate_workout_gemini,
    update_workout_plan,
)

from .schemas import (
    FeedbackRequest,
    UserInput,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


def render_error(
    request: Request,
    message: str,
    code: int = 500
):

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "message": message,
        },
        status_code=code,
    )


@router.get(
    "/",
    response_class=HTMLResponse
)
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        },
    )


@router.post(
    "/generate-workout",
    response_class=HTMLResponse
)
def generate_workout(
    request: Request,

    name: str = Form(...),

    user_id: str = Form(...),

    age: int = Form(...),

    weight: float = Form(...),

    goal: str = Form(...),

    intensity: str = Form(...),

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
        )

        user = save_user(
            db,
            data
        )

        workout = generate_workout_gemini(
            data
        )

        tip = generate_nutrition_tip_with_flash(
            data
        )

        plan = save_plan(
            db,
            user.user_id,
            workout,
            tip,
        )

        return templates.TemplateResponse(

            request=request,

            name="result.html",

            context={

                "request": request,

                "user": user,

                "plan": plan,

                "active_plan": workout,

                "message": None,
            },
        )

    except ValueError as exc:

        return render_error(
            request,
            str(exc),
            422
        )

    except GeminiServiceError as exc:

        return render_error(
            request,
            str(exc),
            503
        )

    except Exception as exc:

        return render_error(
            request,
            f"Unexpected server error: {exc}",
            500
        )


@router.post(
    "/submit-feedback",
    response_class=HTMLResponse
)
def submit_feedback(
    request: Request,

    user_id: str = Form(...),

    feedback: str = Form(...),

    db: Session = Depends(get_db),
):

    try:

        settings = get_settings()

        data = FeedbackRequest(

            user_id=user_id,

            feedback=feedback[
                :settings.max_feedback_length
            ],
        )

        user = get_user(
            db,
            data.user_id
        )

        plan = get_latest_plan(
            db,
            data.user_id
        )

        if not user or not plan:

            return render_error(
                request,
                "User or workout plan was not found.",
                404,
            )

        profile = UserInput(

            name=user.name,

            user_id=user.user_id,

            age=user.age,

            weight=user.weight,

            goal=user.goal,

            intensity=user.intensity,
        )

        revised = update_workout_plan(

            plan.original_plan,

            profile,

            data.feedback,
        )

        update_plan(

            db,

            plan,

            revised,

            data.feedback,
        )

        return templates.TemplateResponse(

            request=request,

            name="result.html",

            context={

                "request": request,

                "user": user,

                "plan": plan,

                "active_plan": revised,

                "message":
                    "Your plan was updated using your feedback.",
            },
        )

    except ValueError as exc:

        return render_error(
            request,
            str(exc),
            422
        )

    except GeminiServiceError as exc:

        return render_error(
            request,
            str(exc),
            503
        )

    except Exception as exc:

        return render_error(
            request,
            f"Unexpected server error: {exc}",
            500
        )


@router.get(
    "/view-all-users",
    response_class=HTMLResponse
)
def view_all_users(
    request: Request,

    token: str = "",

    db: Session = Depends(get_db),
):

    settings = get_settings()

    if (
        settings.admin_token
        and token != settings.admin_token
    ):

        return templates.TemplateResponse(

            request=request,

            name="admin_login.html",

            context={
                "request": request
            },

            status_code=401,
        )

    rows = get_all_users_with_plans(
        db
    )

    return templates.TemplateResponse(

        request=request,

        name="all_users.html",

        context={

            "request": request,

            "rows": rows,
        },
    )


@router.post(
    "/admin-login"
)
def admin_login(
    request: Request,

    token: str = Form(...)
):

    return RedirectResponse(

        url=f"/view-all-users?token={token}",

        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get(
    "/api/health"
)
def health():

    settings = get_settings()

    return {

        "status": "ok",

        "gemini_configured":
            bool(settings.gemini_api_key),
    }


@router.post(
    "/api/generate-workout"
)
def api_generate_workout(
    data: UserInput,

    db: Session = Depends(get_db)
):

    try:

        user = save_user(
            db,
            data
        )

        workout = generate_workout_gemini(
            data
        )

        tip = generate_nutrition_tip_with_flash(
            data
        )

        plan = save_plan(

            db,

            user.user_id,

            workout,

            tip,
        )

        return {

            "user":
                data.model_dump(),

            "plan_id":
                plan.id,

            "workout_plan":
                workout,

            "nutrition_tip":
                tip,
        }

    except GeminiServiceError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc)
        ) from exc


@router.post(
    "/api/submit-feedback"
)
def api_submit_feedback(

    data: FeedbackRequest,

    db: Session = Depends(get_db),
):

    user = get_user(
        db,
        data.user_id
    )

    plan = get_latest_plan(
        db,
        data.user_id
    )

    if not user or not plan:

        raise HTTPException(

            status_code=404,

            detail="User or plan not found"
        )

    profile = UserInput(

        name=user.name,

        user_id=user.user_id,

        age=user.age,

        weight=user.weight,

        goal=user.goal,

        intensity=user.intensity,
    )

    try:

        revised = update_workout_plan(

            plan.original_plan,

            profile,

            data.feedback,
        )

        update_plan(

            db,

            plan,

            revised,

            data.feedback,
        )

        return {

            "plan_id":
                plan.id,

            "updated_plan":
                revised,

            "feedback":
                data.feedback,
        }

    except GeminiServiceError as exc:

        raise HTTPException(

            status_code=503,

            detail=str(exc)
        ) from exc