from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import os
import sqlite3
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==================== GEMINI SETUP (WORKS 100%) ====================
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

model = genai.GenerativeModel(
    'gemini-pro-latest',  
    generation_config={
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 8192,
    },
    # Fixed safety settings — no typos, no tabs!
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)

# ==================== DATABASE SETUP ====================
def init_db():
    with sqlite3.connect('queries.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()  # Creates the DB automatically on first run

def save_query(question: str, answer: str):
    with sqlite3.connect('queries.db') as conn:
        conn.execute("INSERT INTO user_queries (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        stream = data.get('stream', False)

        if not question:
            return jsonify({'success': False, 'error': 'Question cannot be empty'}), 400

        response = model.generate_content(question, stream=True)
        full_answer = ""

        def generate_stream():
            nonlocal full_answer
            try:
                for chunk in response:
                    if not chunk.text:      # Skip blocked/empty chunks
                        continue
                    text = chunk.text
                    full_answer += text
                    yield text
            except Exception as e:
                error = f"\n\n[Error: {str(e)}]"
                yield error
                full_answer += error
            finally:
                if full_answer.strip():
                    save_query(question, full_answer)

        if stream:
            return Response(stream_with_context(generate_stream()), mimetype='text/plain')
        else:
            for chunk in response:
                if chunk.text:
                    full_answer += chunk.text
            save_query(question, full_answer)
            return jsonify({'success': True, 'answer': full_answer})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def history():
    try:
        with sqlite3.connect('queries.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT question, answer, timestamp FROM user_queries ORDER BY timestamp DESC LIMIT 15")
            rows = c.fetchall()
            return jsonify({'success': True, 'history': [dict(row) for row in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)   # debug=True so you can see errors easily