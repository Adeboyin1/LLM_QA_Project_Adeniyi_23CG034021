import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()  # loads .env from current folder

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file!")
    exit()

genai.configure(api_key=api_key)

print("Available Gemini models you can use right now:\n")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print("✅", m.name)

print("\nUse any of the ones with ✅ in your Flask app.")