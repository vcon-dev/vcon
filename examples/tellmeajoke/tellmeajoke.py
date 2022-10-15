# importing Flask and other modules
from flask import Flask, request, render_template, render_template_string
import sys
from pprint import pprint
import secrets
from werkzeug.utils import secure_filename
import os
from flask import jsonify
import json
import datetime



# Our local modules
sys.path.append("../..")

try:
    pprint(sys.path)
    import vcon
except ModuleNotFoundError as e:
    print("ModuleNotFoundError:", e)


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

# Flask constructor
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["DEBUG"] = True
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = secrets.token_bytes(16)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=["POST"])
def post_joke():
    print(request.form)
    print(request.files) 

    try:
        email = request.form.getlist("email")[0]
        print(email)
        file = request.files.getlist('filename')[0]
        print(file)
        if file and allowed_file(file.filename):
            print("Bingo!")
            filename = secure_filename(file.filename)
            print(filename)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(full_path)
            file.save(full_path)


            # Construct empty vCon
            vCon = vcon.Vcon()

            # Add some basic call META data
            vCon.set_party_tel_url(email)
            vCon.set_party_tel_url("ghostofbasho@gmail.com")

            # Timestamp
            now = datetime.datetime.now()
            # Add a recording of the call
            recording_name = full_path
            with open(recording_name, 'rb') as file_handle:
                recording_bytes = file_handle.read()
            vCon.add_dialog_inline_recording(
            recording_bytes,
            now.strftime("%a, %d %b %Y %H:%M:%S -0000"),
            60, # sec. duration
            [0, 1], # parties recorded
            file.mimetype, # MIME type
            recording_name)

            # Serialize the vCon to a JSON format string
            json_string = vCon.dumps()

            # Write the JSON string to a file
            vcon_name = email + ".vcon"
            #open text file
            vcon_path = os.path.join(app.config['UPLOAD_FOLDER'], vcon_name)
            
            #open text file
            vcon_file = open(vcon_path, "w")

            #write string to file
            vcon_file.write(json_string)

            #close file
            vcon_file.close()
            return jsonify(json_string)
    except Exception as e:
        print("Exception:", e)
        return jsonify({"error": str(e)})



@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
