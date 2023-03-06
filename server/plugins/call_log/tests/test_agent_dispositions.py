import vcon
import os
from plugins.call_log import compute_dialog_projection


def test_missed_call():
    vCon = convert_json_to_vcon("missed_call")

    dialog = compute_dialog_projection(vCon.dialog)
    assert dialog[0]["disposition"] == "MISSED"
    assert dialog[1]["disposition"] == "DECLINED"
    assert dialog[2]["disposition"] == "MISSED"
    assert dialog[3]["disposition"] == "HUNG UP"


def test_answered_call():
    vCon = convert_json_to_vcon("answered_call")

    dialog = compute_dialog_projection(vCon.dialog)
    assert dialog[0]["disposition"] == "MISSED"
    assert dialog[1]["disposition"] == "INTERNAL TRANSFER"
    assert dialog[2]["disposition"] == "MISSED"
    assert dialog[3]["disposition"] == "ANSWERED"


def convert_json_to_vcon(file_path):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    file_name = os.path.join(file_dir, f"vcon_fixtures/{file_path}.json")

    vCon = None
    with open(file_name, "r") as f:
        vCon = vcon.Vcon()
        vCon.load(f)
    return vCon
