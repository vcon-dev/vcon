import json
import random
from faker import Faker

fake = Faker()


def generate_mock_vcon():

    vcon = {
        "uuid": fake.uuid4(),
        "vcon": "0.0.1",
        "group": [],
        "dialog": [],
        "parties": [],
        "subject": None,
        "analysis": [],
        "appended": None,
        "redacted": {},
        "created_at": fake.iso8601(),
        "attachments": [],
    }

    num_dialogs = random.randint(1, 5)
    for i in range(num_dialogs):
        vcon["dialog"].append(
            {
                "alg": "SHA-512",
                "url": fake.url(),
                "body": None,
                "meta": {
                    "direction": random.choice(["in", "out"]),
                    "disposition": random.choice(
                        ["ANSWERED", "FAILED", "NO ANSWER", "BUSY"]
                    ),
                },
                "type": "recording",
                "start": fake.iso8601(),
                "parties": [0, 1],
                "duration": random.randint(60, 600),
                "encoding": None,
                "filename": None,
                "mimetype": "audio/x-wav",
                "signature": fake.sha256(),
            }
        )

    num_parties = random.randint(1, 5)
    for i in range(num_parties):
        vcon["parties"].append(
            {
                "tel": fake.phone_number(),
                "meta": {"role": random.choice(["agent", "customer"])},
                "name": fake.name(),
                "stir": None,
                "jcard": None,
                "gmlpos": None,
                "mailto": fake.email(),
                "timezone": None,
                "validation": None,
                "civicaddress": None,
            }
        )

    num_analysis = random.randint(1, 5)
    for i in range(num_analysis):
        vcon["analysis"].append(
            {
                "body": json.dumps(
                    {
                        "words": [],
                        "confidence": random.random(),
                        "paragraphs": {"paragraphs": []},
                        "transcript": fake.text(),
                    }
                ),
                "type": random.choice(["transcript", "summary"]),
                "dialog": random.randint(0, num_dialogs),
                "vendor": random.choice(["ibm", "google", "amazon"]),
                "encoding": "json",
            }
        )

    num_attachments = random.randint(0, 5)
    for i in range(num_attachments):
        vcon["attachments"].append(
            {
                "alg": None,
                "url": None,
                "body": fake.text(),
                "type": "strolid_dealer",
                "party": None,
                "encoding": "none",
                "filename": None,
                "mimetype": None,
                "signature": None,
            }
        )

    return vcon
