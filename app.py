from flask import Flask, redirect, render_template, request, session, url_for, make_response
import sqlite3

app = Flask(__name__)
app.secret_key = 'vovavovavova'

@app.route("/")
def index():

    return render_template(
        "index.html"
        )

@app.route("/products")
def products():

    return render_template(
        "products.html"
        )

@app.route("/racion")
def racion():

    return render_template(
        "racion.html"
        )

@app.route("/control")
def control():

    return render_template(
        "control.html"
        )

@app.route("/calories")
def calories():

    return render_template(
        "calories.html"
        )



if __name__ == "__main__":
    app.run(debug=True)
