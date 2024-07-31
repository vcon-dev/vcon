""" Module for creating a SCITT signed statement """

import hashlib
import json
import argparse

from typing import Optional

from pycose.messages import Sign1Message
from pycose.headers import Algorithm, KID, ContentType
from pycose.algorithms import Es256
from pycose.keys.curves import P256
from pycose.keys.keyparam import KpKty, EC2KpD, EC2KpX, EC2KpY, KpKeyOps, EC2KpCurve
from pycose.keys.keytype import KtyEC2
from pycose.keys.keyops import SignOp, VerifyOp
from pycose.keys import CoseKey

from ecdsa import SigningKey, VerifyingKey

# CWT header label comes from version 4 of the scitt architecture document
# https://www.ietf.org/archive/id/draft-ietf-scitt-architecture-04.html#name-issuer-identity
HEADER_LABEL_CWT = 13

# Various CWT header labels come from:
# https://www.rfc-editor.org/rfc/rfc8392.html#section-3.1
HEADER_LABEL_CWT_ISSUER = 1
HEADER_LABEL_CWT_SUBJECT = 2

# CWT CNF header labels come from:
# https://datatracker.ietf.org/doc/html/rfc8747#name-confirmation-claim
HEADER_LABEL_CWT_CNF = 8
HEADER_LABEL_CNF_COSE_KEY = 1


def open_signing_key(key_file: str) -> SigningKey:
    """
    opens the signing key from the key file.
    NOTE: the signing key is expected to be a P-256 ecdsa key in PEM format.
    """
    with open(key_file, encoding="UTF-8") as file:
        signing_key = SigningKey.from_pem(file.read(), hashlib.sha256)
        return signing_key


def open_payload(payload_file: str) -> str:
    """
    opens the payload from the payload file.
    NOTE: the payload is expected to be in json format.
          however, any payload of type bytes is allowed.
    """
    with open(payload_file, encoding="UTF-8") as file:
        payload = json.loads(file.read())

        # convert the payload to a cose sign1 payload
        payload = json.dumps(payload, ensure_ascii=False)

        return payload


def create_signed_statement(
    signing_key: SigningKey,
    payload: str,
    subject: str,
    issuer: str,
    content_type: str,
) -> bytes:
    """
    creates a signed statement, given the signing_key, payload, issuer and subject
    """

    verifying_key: Optional[VerifyingKey] = signing_key.verifying_key
    assert verifying_key is not None

    # pub key is the x and y parts concatenated
    xy_parts = verifying_key.to_string()

    # ecdsa P256 is 64 bytes
    x_part = xy_parts[0:32]
    y_part = xy_parts[32:64]

    # create a protected header where
    #  the verification key is attached to the cwt claims
    protected_header = {
        Algorithm: Es256,
        KID: b"testkey",
        ContentType: content_type,
        HEADER_LABEL_CWT: {
            HEADER_LABEL_CWT_ISSUER: issuer,
            HEADER_LABEL_CWT_SUBJECT: subject,
            HEADER_LABEL_CWT_CNF: {
                HEADER_LABEL_CNF_COSE_KEY: {
                    KpKty: KtyEC2,
                    EC2KpCurve: P256,
                    EC2KpX: x_part,
                    EC2KpY: y_part,
                },
            },
        },
    }

    # create the statement as a sign1 message using the protected header and payload
    statement = Sign1Message(phdr=protected_header, payload=payload.encode("utf-8"))

    # create the cose_key to sign the statement using the signing key
    cose_key = {
        KpKty: KtyEC2,
        EC2KpCurve: P256,
        KpKeyOps: [SignOp, VerifyOp],
        EC2KpD: signing_key.to_string(),
        EC2KpX: x_part,
        EC2KpY: y_part,
    }

    cose_key = CoseKey.from_dict(cose_key)
    statement.key = cose_key

    # sign and cbor encode the statement.
    # NOTE: the encode() function performs the signing automatically
    signed_statement = statement.encode([None])

    return signed_statement


def main():
    """Creates a signed statement"""

    parser = argparse.ArgumentParser(description="Create a signed statement.")

    # signing key file
    parser.add_argument(
        "--signing-key-file",
        type=str,
        help="filepath to the stored ecdsa P-256 signing key, in pem format.",
        default="scitt-signing-key.pem",
    )

    # payload-file (a reference to the file that will become the payload of the SCITT Statement)
    parser.add_argument(
        "--payload-file",
        type=str,
        help="filepath to the content that will become the payload of the SCITT Statement "
        "(currently limited to json format).",
        default="scitt-payload.json",
    )

    # content-type
    parser.add_argument(
        "--content-type",
        type=str,
        help="The iana.org media type for the payload",
        default="application/json",
    )

    # subject
    parser.add_argument(
        "--subject",
        type=str,
        help="identifies the artifact that is the subject of the statement, enabling correlation.",
    )

    # issuer
    parser.add_argument(
        "--issuer",
        type=str,
        help="issuer who owns the signing key.",
    )

    # output file
    parser.add_argument(
        "--output-file",
        type=str,
        help="name of the output file to store the signed statement.",
        default="signed-statement.cbor",
    )

    args = parser.parse_args()

    signing_key = open_signing_key(args.signing_key_file)
    payload = open_payload(args.payload_file)

    signed_statement = create_signed_statement(
        signing_key,
        payload,
        args.subject,
        args.issuer,
        args.content_type,
    )

    with open(args.output_file, "wb") as output_file:
        output_file.write(signed_statement)


if __name__ == "__main__":
    main()
