from flask import Flask, redirect, render_template, request, session, url_for, make_response
import sqlite3
from openai import OpenAI, RateLimitError, APIError
import requests
import uuid
import dotenv
import os

app = Flask(__name__)
app.secret_key = 'vovavovavova'
dotenv.load_dotenv()

@app.route("/")
def index():

    if 'user' not in session:
        session['user'] = str(uuid.uuid4()) 
    
    user = session.get('user')
    return render_template(
        "index.html",
        user=user
        )

openrouter_key = os.getenv("KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key,
)

system_prompt = """
    Ты - диетолог
    Твоя цель исходя, из 5 вопросов написать вывод о диете которая предпочтительна пользователю
    Сохраняй доброжелательный тон
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

    except:
        return "не получилось"

QUEST = [
    "Что есть в холодильнике?",
    "Что ты ешь каждый день?",
    "Как часто занимаешься спортом?",
    "Какая цель диеты?",
    "Есть ли аллергии или предпочтения в еде?"
]

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    
    user_id = session['user']
    answer = None

    if 'quest_cnt' not in session:
        session['quest_cnt'] = 0
        session['answers'] = []
    
    if request.method == 'POST':
        text = request.form.get('question', '').strip()
        
        if text:
            session['answers'].append(text)
            session['quest_cnt'] = session['quest_cnt'] + 1
            
            if session['quest_cnt'] == 5:

                ans = ""
                for i in range(5):
                    ans = ans + str(i+1) + ". " + QUEST[i] + " - " + session['answers'][i] + "\n"
                
                answer = get_ans(user_id, ans)
                
                session['quest_cnt'] = 0
                session['answers'] = []
    

    return render_template('chat.html', 
                         answer=answer, 
                         questions=QUEST,
                         cur=session['quest_cnt'],
                         answers=session['answers'])




if __name__ == "__main__":
    app.run(debug=True)
