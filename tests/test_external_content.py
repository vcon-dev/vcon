"""
Unit tests for external content such as recording, attachments which are stored
as URLs with a signature for the content stored else where.  Using
Leighton-Micali One Time Signature (RFC8554).
"""

import os
import pytest
import vcon
import vcon.security
import hsslms

def test_lm_ots_sign() -> None:
  file_size = 2048
  fake_file = os.urandom(file_size)

  key, sig = vcon.security.lm_one_time_signature(fake_file)

  vcon.security.verify_lm_one_time_signature(fake_file, sig, key)

  try:
    # cause signature to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig.replace("D", "E", 1), key)
    raise Exception("Should have raisee and INVALID signature error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

  try:
    # cause key to fail
    vcon.security.verify_lm_one_time_signature(fake_file, sig, key.replace("A", "Z", 1))
    raise Exception("Should have raised and INVALID key error")

  except hsslms.utils.INVALID as invalid_error:
    # Expect this to be raised as we have modified signature
    pass

