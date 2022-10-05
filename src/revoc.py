from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def pg():
    if request.method == "POST":

        return "Working"
    return render_template("revoc.html")