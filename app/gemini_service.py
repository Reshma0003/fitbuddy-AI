from functools import lru_cache

from google import genai
from google.genai import types

from .config import settings


SAFETY_NOTE = """
This application provides general wellness guidance and is not a medical
diagnostic or treatment service.

Do not diagnose injuries or medical conditions.
Do not prescribe medication.
Do not recommend extreme dieting.
Keep recommendations practical and conservative.

If a person has a medical condition, injury, pregnancy,
or unusual symptoms, recommend consulting a qualified healthcare professional.
"""


def fallback_plan(
    name: str,
    goal: str,
    intensity: str,
    experience: str,
) -> str:

    return f"""
FITBUDDY - 7 DAY FITNESS PLAN

Name: {name}
Goal: {goal.title()}
Intensity: {intensity.title()}
Experience: {experience.title()}

--------------------------------
DAY 1 - FULL BODY FOUNDATION
--------------------------------

Warm-up:
5-10 minutes of easy walking and mobility.

Workout:
• Bodyweight squats - 3 x 10
• Incline push-ups - 3 x 8
• Glute bridges - 3 x 12
• Plank - 3 x 20 seconds

Cooldown:
5 minutes of gentle stretching.


--------------------------------
DAY 2 - CARDIO AND CORE
--------------------------------

Warm-up:
5 minutes of easy movement.

Workout:
• Brisk walking/cycling - 20-30 minutes
• Dead bug - 3 x 8 each side
• Bird dog - 3 x 8 each side

Recovery:
Hydrate and take a light walk later if comfortable.


--------------------------------
DAY 3 - LOWER BODY
--------------------------------

Warm-up:
5-10 minutes of mobility.

Workout:
• Squats - 3 x 10
• Reverse lunges - 3 x 8 each side
• Calf raises - 3 x 15
• Glute bridges - 3 x 12

Cooldown:
Gentle lower-body stretching.


--------------------------------
DAY 4 - ACTIVE RECOVERY
--------------------------------

Activity:

• Easy walking - 20-30 minutes
• Mobility - 10 minutes
• Optional beginner yoga

Keep the effort comfortable.


--------------------------------
DAY 5 - UPPER BODY
--------------------------------

Warm-up:
5 minutes of shoulder and arm mobility.

Workout:
• Incline push-ups - 3 x 8
• Resistance-band rows - 3 x 12
• Shoulder raises - 2 x 10
• Plank - 3 x 20 seconds

Cooldown:
Upper-body stretching.


--------------------------------
DAY 6 - CONDITIONING
--------------------------------

Warm-up:
5-10 minutes of easy cardio.

Workout:

4 rounds:

30 seconds moderate cardio
60 seconds easy recovery

Then:

• Core exercise - 2-3 sets
• Mobility - 5 minutes


--------------------------------
DAY 7 - REST AND RECOVERY
--------------------------------

• Rest
• Light walking if comfortable
• Hydration
• Good sleep
• Gentle stretching if desired


PROGRESSION:

Increase exercise volume gradually.
Avoid making large sudden increases.

Stop exercise if you experience sharp pain,
dizziness, chest pain, or unusual shortness of breath.
"""


def fallback_tip(goal: str) -> str:

    tips = {

        "weight loss":
            "Build meals around vegetables, a protein source, "
            "whole-food carbohydrates and water. Focus on consistent "
            "healthy habits instead of extreme food restriction.",

        "muscle gain":
            "Include a protein-rich food at regular meals and combine "
            "resistance training with adequate sleep and recovery.",

        "general wellness":
            "Aim for balanced meals, regular movement, adequate hydration "
            "and a consistent sleep routine.",

        "flexibility":
            "Pair regular mobility work with balanced meals and adequate "
            "hydration to support recovery.",

        "endurance":
            "Hydrate regularly and include carbohydrate-rich whole foods "
            "around longer or harder training sessions.",
    }

    return tips.get(
        goal,
        tips["general wellness"],
    )


@lru_cache
def get_client():

    if not settings.gemini_api_key:
        return None

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_with_gemini(
    model: str,
    prompt: str,
    temperature: float = 0.4,
) -> str:

    client = get_client()

    if client is None:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=5000,
        ),
    )

    text = (response.text or "").strip()

    if not text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return text


def generate_workout_gemini(user):

    prompt = f"""
You are FitBuddy, an AI fitness planning assistant.

Create a personalized 7-day general wellness workout plan.

USER INFORMATION:

Name:
{user.name}

Age:
{user.age}

Weight:
{user.weight} kg

Fitness goal:
{user.goal}

Workout intensity:
{user.intensity}

Experience:
{user.experience_level}


REQUIRED OUTPUT:

Create exactly:

Day 1
Day 2
Day 3
Day 4
Day 5
Day 6
Day 7

For each day include:

1. Workout focus
2. Warm-up
3. Main exercises
4. Sets/repetitions or duration
5. Rest guidance
6. Cooldown/recovery

Include at least one recovery/rest day.

Keep the difficulty appropriate for the user's
selected intensity and experience level.

Avoid unsupported promises about weight loss,
muscle gain or health outcomes.

{SAFETY_NOTE}
"""

    try:

        result = generate_with_gemini(
            settings.workout_model,
            prompt,
            temperature=0.4,
        )

        return result, True

    except Exception:

        return (
            fallback_plan(
                user.name,
                user.goal,
                user.intensity,
                user.experience_level,
            ),
            False,
        )


def generate_nutrition_tip_with_flash(
    goal: str,
):

    prompt = f"""
You are the FitBuddy nutrition and recovery assistant.

Fitness goal:
{goal}

Give one concise and practical nutrition
or recovery recommendation.

Requirements:

• 2-4 sentences
• Easy language
• Practical advice
• No extreme dieting
• No medical diagnosis
• No medication recommendations
• No unsupported medical claims

{SAFETY_NOTE}
"""

    try:

        result = generate_with_gemini(
            settings.fast_model,
            prompt,
            temperature=0.3,
        )

        return result, True

    except Exception:

        return (
            fallback_tip(goal),
            False,
        )


def update_workout_plan(
    user,
    original_plan: str,
    feedback: str,
):

    prompt = f"""
You are FitBuddy.

Update an existing 7-day fitness plan based
on user feedback.

USER:

Name:
{user.name}

Age:
{user.age}

Weight:
{user.weight} kg

Goal:
{user.goal}

Intensity:
{user.intensity}

Experience:
{user.experience_level}


ORIGINAL PLAN:

{original_plan}


USER FEEDBACK:

{feedback}


TASK:

Create a revised 7-day workout plan.

The revised plan must:

• Address the user's feedback.
• Keep the user's fitness goal.
• Keep the requested intensity.
• Be realistic.
• Include warm-up.
• Include main exercises.
• Include rest guidance.
• Include cooldown/recovery.
• Include at least one recovery day.

Do not diagnose medical conditions.

Do not prescribe medication.

Do not recommend extreme dieting.

{SAFETY_NOTE}
"""

    try:

        result = generate_with_gemini(
            settings.workout_model,
            prompt,
            temperature=0.4,
        )

        return result, True

    except Exception:

        fallback = (
            original_plan
            + "\n\n"
            + "--------------------------------\n"
            + "FEEDBACK APPLIED\n"
            + "--------------------------------\n"
            + f"Requested modification:\n{feedback}\n\n"
            + "Please apply this change conservatively."
        )

        return fallback, False