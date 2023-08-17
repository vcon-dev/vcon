import vcon_fixture
import json
import sys
import httpx

# See if there's a command line argument for the number of vCons to generate
if len(sys.argv) > 1:
    num_vcons = int(sys.argv[1])
else:
    num_vcons = 1

# Generate the vCons
for i in range(num_vcons):
    vcon = vcon_fixture.generate_mock_vcon()
    # Post the vCon to the server
    print(json.dumps(vcon, indent=4))
    r = httpx.post("http://localhost:8000/vcon", json=vcon)
    print(r.status_code)
    print(r.text)
    
