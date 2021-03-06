"""
Unit test for date conversions
"""

import vcon.utils

date_int = 1652552179
date_float = 1652552179.0001
date_rfc2822 = "Wed, 14 May 2022 18:16:19 -0000"
date_rfc3339 = "2022-05-14T18:16:19.000+00:00"
date_rfc3339_EDT = "2022-05-14T14:16:19.000-04:00"


def test_cannonize_date():
  cannonized = vcon.utils.cannonize_date(date_int)
  #print(cannonized)
  assert(cannonized == date_rfc3339)

  cannonized = vcon.utils.cannonize_date(date_float)
  # off by time zone
  #print(cannonized)
  assert(cannonized == date_rfc3339)

  cannonized = vcon.utils.cannonize_date(date_rfc2822)
  # off by time zone
  #print(cannonized)
  assert(cannonized == date_rfc3339)

  cannonized = vcon.utils.cannonize_date(date_rfc3339)
  # off by time zone
  #print(cannonized)
  assert(cannonized == date_rfc3339)

  cannonized = vcon.utils.cannonize_date(date_rfc3339_EDT)
  # off by time zone
  #print(cannonized)
  assert(cannonized == date_rfc3339)

  try:
    cannonized = vcon.utils.cannonize_date("10 June 2022 8:55PM")
    raise Exception("Should have raised AttributeError exception for not valid date format")

  except AttributeError as e:
    # Expect to catch exception here
    pass

