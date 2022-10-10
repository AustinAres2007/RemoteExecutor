
from flask import Flask, render_template, request, redirect, url_for
import client

app = Flask(__name__)
    
def output(message):
    with app.app_context():
        return str(message)

@app.route("/", methods=["GET", "POST"])
def send_command():

    with app.app_context():
        try:
            c.send_command(request.form.get("cmdin"))
        except KeyError:
            output("Not a valid command.")

    return request.form.get("cmdin")

@app.route("/client", methods=["GET", "POST"])
def validate_password():

    if request.method == "POST":
        global c
        c = client.RemoteExecutorClient(False, True, request.form.get("password"), output)
        c.listen_for_commands()

        return render_template("revoc.html")

    return render_template("login.html")