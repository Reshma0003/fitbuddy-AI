from functools import lru_cache
import time

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from .config import get_settings
from .schemas import UserInput


class GeminiServiceError(RuntimeError):
    pass


@lru_cache
def get_client():
    settings = get_settings()

    if genai is None:
        raise GeminiServiceError(
            "google-genai is not installed. "
            "Run: pip install -r requirements.txt"
        )

    if not settings.gemini_api_key:
        raise GeminiServiceError(
            "GEMINI_API_KEY is not configured. "
            "Add it to the .env file and restart the server."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def _generate(
    model: str,
    prompt: str,
    max_tokens: int = 5000
) -> str:

    client = get_client()

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=max_tokens,
                ),
            )

            text = (response.text or "").strip()

            if not text:
                raise GeminiServiceError(
                    "Gemini returned an empty response."
                )

            return text

        except GeminiServiceError:
            raise

        except Exception as exc:

            error_message = str(exc)

            # Retry temporary Gemini availability errors
            if "503" in error_message or "UNAVAILABLE" in error_message:

                if attempt < max_retries - 1:

                    wait_time = 5 * (attempt + 1)

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

            raise GeminiServiceError(
                f"Gemini request failed: {exc}"
            ) from exc

    raise GeminiServiceError(
        "Gemini request failed after multiple retries."
    )


def generate_workout_gemini(
    user: UserInput
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy, a responsible AI fitness-planning assistant.

Create a personalized 7-day workout plan.

USER DETAILS:

Name: {user.name}

Age: {user.age}

Weight: {user.weight} kg

Fitness goal: {user.goal}

Workout intensity: {user.intensity}


REQUIREMENTS:

1. Create exactly 7 labeled days.

2. Use Day 1 through Day 7.

3. Every day must contain:

Focus
Warm-up
Main workout
Cooldown or recovery

4. Include exercise names.

5. Include sets and repetitions or duration.

6. Include suitable rest periods.

7. Match the requested intensity.

8. Include reasonable rest/recovery.

9. Do not recommend dangerous exercises.

10. Do not prescribe medication.

11. Do not recommend extreme dieting.

12. Do not diagnose medical conditions.

13. Keep the response readable.

14. Add a short safety note at the end.

The safety note should remind the user that this is
general wellness information and that they should stop
exercise if they experience pain, dizziness, or other
concerning symptoms.
"""

    return _generate(
        settings.gemini_workout_model,
        prompt,
        6000
    )


def generate_nutrition_tip_with_flash(
    user: UserInput
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Give ONE concise and practical nutrition or recovery tip.

USER PROFILE:

Age: {user.age}

Weight: {user.weight} kg

Fitness goal: {user.goal}

Workout intensity: {user.intensity}


RULES:

- Keep the answer under 120 words.
- Focus on balanced food.
- Mention hydration when useful.
- Mention recovery or sleep when useful.
- Prefer ordinary foods.
- Do not prescribe medicine.
- Do not prescribe supplements.
- Do not recommend extreme diets.
- Do not diagnose health conditions.

End with a short reminder that individualized
medical/nutrition advice should come from a qualified
professional when needed.
"""

    return _generate(
        settings.gemini_tip_model,
        prompt,
        500
    )


def update_workout_plan(
    original_plan: str,
    user: UserInput,
    feedback: str
) -> str:

    settings = get_settings()

    prompt = f"""
You are updating an existing FitBuddy fitness plan.

USER PROFILE:

Name: {user.name}

Age: {user.age}

Weight: {user.weight} kg

Fitness goal: {user.goal}

Workout intensity: {user.intensity}


ORIGINAL PLAN:

--------------------

{original_plan}

--------------------


USER FEEDBACK:

--------------------

{feedback}

--------------------


TASK:

Create a COMPLETE revised 7-day workout plan.

Do not return only the changed lines.

Apply the user's feedback where it is reasonable.

Preserve useful parts of the original plan.

Keep the plan safe.

For every day include:

- Focus
- Warm-up
- Main workout
- Cooldown/recovery

Include a short safety note.

Do not prescribe medication.

Do not recommend extreme dieting.

Do not diagnose medical conditions.
"""

    return _generate(
        settings.gemini_workout_model,
        prompt,
        6000
    )