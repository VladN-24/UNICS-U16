from flask import Flask, redirect, render_template, request, session, url_for, make_response
import sqlite3
from openai import OpenAI, RateLimitError, APIError
import requests
import uuid
import dotenv
import os
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'vovavovavova'
dotenv.load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = Path(tempfile.gettempdir()) / "flask_two_pages_app.sqlite3"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(cursor, table, column):
    cursor.execute(f'PRAGMA table_info({table})')
    return any(row['name'] == column for row in cursor.fetchall())


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        kkal INTEGER NOT NULL,
        date INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


init_db()


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
    Ты диетолог-консультант. Отвечай сразу готовым ответом, без объяснений и размышлений.
    ПРАВИЛА:
    екомендации: тип диеты, калорийность, 3-4 совета с примерами
    5. Не повторяй вопросы пользователя
    6. Не показывай свои размышления - только готовый ответ
    Твой ответ должен начинаться сразу с рекомендаций. Никаких вступлений вроде "я подумал" или "давайте разберем".
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
    "Какой у вас рост, вес, пол и возраст",
    "Как часто вы питаетесь?",
    "Какой у вас образ жизни?",
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
                    ans = ans + str(i + 1) + ". " + QUEST[i] + " - " + session['answers'][i] + "\n"

                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products WHERE user_id = ?', (user_id,))
                products = cursor.fetchall()
                conn.close()

                if products:
                    ans = ans + "\nпродукты в холодильнике:\n"
                    for product in products:
                        ans = ans + "- " + product['name'] + " (" + str(product['kkal']) + " ккал, срок " + str(
                            product['date']) + " дней)\n"
                else:
                    ans = ans + "\nВ холодильнике ничего нет\n"

                ans = ans + """\nТы — экспертный диетолог-аналитик. Твоя задача: на основе полученных данных сформировать персональную стратегию питания.
    Нельзя повторять вопросы пользователя и пересказывать его ответы. 
    Сразу переходи к делу. Надо рассказать четко о типе диеты, калорийности в день, и 3-4 рекомендациях.
    Сохраняй доброжелательнй тон
    Ответ должен быть строго по существу.
    Ответ должен быть исключительно на русском языке"""

                answer = get_ans(user_id, ans)

                session['quest_cnt'] = 0
                session['answers'] = []

    return render_template('chat.html',
                           answer=answer,
                           questions=QUEST,
                           cur=session['quest_cnt'],
                           answers=session['answers'])


@app.route("/holodilnik", methods=['GET', 'POST'])
def holodilnik():
    if 'user' not in session:
        return redirect(url_for('index'))

    user_id = session['user']
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        kkal = request.form.get('kkal', '').strip()
        date = request.form.get('date', '').strip()

        if name and kkal and date:
            cursor.execute(
                'INSERT INTO products (user_id, name, kkal, date) VALUES (?, ?, ?, ?)',
                (user_id, name, kkal, date)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('holodilnik'))

    cursor.execute('SELECT * FROM products WHERE user_id = ?', (user_id,))
    products = cursor.fetchall()
    conn.close()

    return render_template('holodilnik.html', products=products)


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user' not in session:
        return redirect(url_for('index'))

    user_id = session['user']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'DELETE FROM products WHERE id = ? AND user_id = ?',
        (product_id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('holodilnik'))


if __name__ == "__main__":
    app.run(debug=True)
