# importing Flask and other modules
from flask import Flask, request, render_template, session
import sys
from pprint import pprint
from flask import session
import secrets
import json



# Our local modules
sys.path.append("/Users/thomashowe/Documents/GitHub/vcon")

try:
    pprint(sys.path)
    import vcon
except ModuleNotFoundError as e:
    print("ModuleNotFoundError:", e)


# Flask constructor
app = Flask(__name__)
app.config["DEBUG"] = True
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = secrets.token_bytes(16)

# A decorator used to tell the application
# which URL is associated function


@app.route('/', methods=["POST"])
def post_update():
    first_name = request.form.get("fname")
    last_name = request.form.get("lname")
    return "Your name is "+first_name + last_name


@app.route('/', methods=["GET"])
def index():
    if vcon not in session:
        the_vcon = vcon.Vcon()
        session['vcon'] = the_vcon.dumps()
    else:
        the_vcon = json.loads(session['vcon'])

    pprint(the_vcon)
    return render_template("index.html", vcon=the_vcon)


if __name__ == '__main__':
    app.run()
