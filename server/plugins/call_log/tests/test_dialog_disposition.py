from plugins.call_log import dialog_disposition


def test_it_should_return_no_answer_for_outbound():
    dialog = {"direction": "out", "disposition": "MISSED"}
    assert dialog_disposition(dialog) == "NO ANSWER"
