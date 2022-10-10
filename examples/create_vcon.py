import sys
sys.path.append("..")

import vcon

# Construct empty vCon
vCon = vcon.Vcon()

# Add some basic call META data
caller = "+18881234567"
called = "1234"
vCon.set_party_tel_url(caller)
vCon.set_party_tel_url(called)

# Add a recording of the call
recording_name = "agent_sample.wav"
with open(recording_name, 'rb') as file_handle:
      recording_bytes = file_handle.read()
vCon.add_dialog_inline_recording(
  recording_bytes,
  "Mon, 23 May 2022 20:09:01 -0000",
  23.5, # sec. duration
  [0, 1], # parties recorded
  "audio/x-wav", # MIME type
  recording_name)

# Serialize the vCon to a JSON format string
json_string = vCon.dumps()
print(json_string)