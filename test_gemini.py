from google import genai
from app.config import get_settings

settings = get_settings()

client = genai.Client(
    api_key=settings.gemini_api_key
)

print("Testing Gemini...")
print("Model:", settings.gemini_workout_model)

response = client.models.generate_content(
    model=settings.gemini_workout_model,
    contents="Reply with exactly: FitBuddy Gemini test successful."
)

print("\nGEMINI OUTPUT:")
print(response.text)