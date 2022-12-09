"""
Unit test for date conversions
"""

import vcon.utils
import datetime
import dateutil.tz

date_int = 1652552179
date_float = 1652552179.0001
date_rfc2822 = "Wed, 14 May 2022 18:16:19 -0000"
date_rfc3339 = "2022-05-14T18:16:19.000+00:00"
date_rfc3339_EDT = "2022-05-14T14:16:19.000-04:00"


def test_created_at():
  v = vcon.Vcon()
  print("created_at: {}".format(v.created_at))
  assert(len(v.created_at) > 10)

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

  datetime_val = datetime.datetime(2022, 9, 27, 14, 23, 38, 938223)
  datetime_val = datetime_val.replace(tzinfo = dateutil.tz.gettz('US/Eastern'))
  cannonized = vcon.utils.cannonize_date(datetime_val)
  #print("{} dst: {}".format(cannonized, datetime_val.dst()))
  assert(cannonized == "2022-09-27T18:23:38.938+00:00")

