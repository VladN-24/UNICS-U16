from flask import Flask, redirect, render_template, request, session, url_for, make_response
import sqlite3
from openai import OpenAI, RateLimitError, APIError
import requests
import uuid

app = Flask(__name__)
app.secret_key = 'vovavovavova'


@app.route("/")
def index():

    if 'user' not in session:
        session['user'] = str(uuid.uuid4())  # <-- генерируем ID
    
    user = session.get('user')
    return render_template(
        "index.html",
        user=user
        )

openrouter_key = "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"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key,
)

system_prompt = """
    Ты - человек, который следит за каллориями. ты должен по продукту, который вводит пользователь вывести каллорийность
"""

users_history = {}

def get_ans(user_id, data):
    try:
        if user_id not in users_history:
            users_history[user_id] = [
                {"role": "system", "content": system_prompt}
            ]
        
        users_history[user_id].append({"role": "user", "content": data})
        
        messages = users_history[user_id][-10:]
        
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        if answer is None:
            return "None"

        users_history[user_id].append({"role": "assistant", "content": answer})

        return answer.strip()

    except RateLimitError:
        return "перегрузка"
    except APIError:
        return "Ошибка API"

    except Exception as e:
        return f"Произошла ошибка при получении ответа: {str(e)}"

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    
    user_id = session['user']
    answer = None
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            answer = get_ans(user_id, question)
    
    return render_template('chat.html', answer=answer)



if __name__ == "__main__":
    app.run(debug=True)
