import sys
import whisper
import os
from io import BytesIO

sys.path.append("..")

import vcon

# Construct empty vCon
try:
    input_vcon = sys.argv[1]
except IndexError:
    input_vcon = "test.vcon"

try:
    output_vcon = sys.argv[2]
except IndexError:
    output_vcon = "transcribed.vcon"
    

input_file = open(input_vcon, 'r')
vCon = vcon.Vcon()
vCon.loads(input_file.read())
input_file.close()


try:
    model = whisper.load_model("base")
    # Load the audio from the vCon, use a temporary
    # file to avoid loading the entire audio into memory
    bytes = vCon.decode_dialog_inline_recording(0)
    tmp_file = open("_temp_file", 'wb')
    tmp_file.write(bytes)
    tmp_file.close()

    # load audio and pad/trim it to fit 30 seconds
    result = model.transcribe("_temp_file", fp16=False, verbose=True)
    print(result)
    os.remove("_temp_file")
    vCon.add_analysis_transcript(0, result, "whisper-ai")
    output_file = open(output_vcon, 'w')
    output_file.write(vCon.dumps())
    output_file.close()

except Exception as e:
    print("Error: {}".format(e))
