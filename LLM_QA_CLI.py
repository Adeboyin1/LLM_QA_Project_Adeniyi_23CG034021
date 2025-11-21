# LLM_QA_CLI.py
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-pro-latest')

def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)   # remove punctuation
    tokens = text.split()
    return " ".join(tokens)

while True:
    question = input("\nAsk a question (or type 'quit' to exit): ").strip()
    if question.lower() in ['quit', 'exit', 'bye']:
        break
    if not question:
        print("Please type something!")
        continue

    processed = preprocess(question)
    print(f"Processed: {processed}")

    try:
        response = model.generate_content(question)
        print("\nAnswer:")
        print(response.text)
    except Exception as e:
        print("Error:", e)