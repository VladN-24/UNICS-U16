from flask import Flask, redirect, render_template, request, session, url_for, make_response
import sqlite3

app = Flask(__name__)
app.secret_key = 'vovavovavova'

@app.route("/")
def index():

    return render_template(
        "index.html"
        )



if __name__ == "__main__":
    app.run(debug=True)
