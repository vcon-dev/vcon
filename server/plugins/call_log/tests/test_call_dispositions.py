import vcon
import os
from plugins.call_log import get_main_agent_and_disposition


def test_lost_call():
    vCon = convert_json_to_vcon("lost_call")

    agent, main_disposition = get_main_agent_and_disposition(vCon)
    assert main_disposition == "LOST"
    assert agent["name"] == "Nicco Alonzo"


def test_answered_call():
    vCon = convert_json_to_vcon("answered_call")

    agent, main_disposition = get_main_agent_and_disposition(vCon)
    assert main_disposition == "ANSWERED"
    assert agent["name"] == "Henrietta Nnabuife"


def test_hung_up_call():
    vCon = convert_json_to_vcon("hung_up_call")

    agent, main_disposition = get_main_agent_and_disposition(vCon)
    assert main_disposition == "HUNG UP"
    assert agent["name"] == "Ricky Willette"


def test_lost_internal_transfer_call():
    vCon = convert_json_to_vcon("lost_internal_transfer_call")

    agent, main_disposition = get_main_agent_and_disposition(vCon)
    assert main_disposition == "LOST INTERNAL TRANSFER"
    assert agent["name"] == "Henrietta Nnabuife"


def test_no_answer_call():
    vCon = convert_json_to_vcon("no_answer_call")

    agent, main_disposition = get_main_agent_and_disposition(vCon)
    assert main_disposition == "NO ANSWER"
    assert agent["name"] == "Ricky Willette"


def convert_json_to_vcon(file_path):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    file_name = os.path.join(file_dir, f"vcon_fixtures/{file_path}.json")

    vCon = None
    with open(file_name, "r") as f:
        vCon = vcon.Vcon()
        vCon.load(f)
    return vCon
