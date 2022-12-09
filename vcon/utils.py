""" Utilities and helper functions for the vcon package """

import datetime
import email.utils
import typing

def epoch_to_rfc2822(time : typing.Union[int, float]) -> str:
  """ Returns RFC2822 date for given epoch time """
  date_string = email.utils.formatdate(float(time))
  return(date_string)

def epoch_to_rfc3339(time : typing.Union[int, float]) -> str:
  """ Returns RFC3339 date for given epoch time """
  # This does the epoch conversion to local time zone.
  date_time = datetime.datetime.utcfromtimestamp(float(time))
  # Assume UTC
  #print("datatime: {} tz: {}".format(date_time, date_time.tzinfo))
  date_time = date_time.replace(tzinfo = datetime.timezone.utc)
  #print("datatime utc: {} tz: {}".format(date_time, date_time.tzinfo))
  date_string = date_time.isoformat('T', timespec='milliseconds')
  return(date_string)

def cannonize_date(date : typing.Union[int, float, str, datetime.datetime]) -> str:
  """
  Convert date to cannonical RFC3339 date format string

  Parameters:
    date Union[int, float, str, datetime.datetime]: date to be cannonized.
    int or float are seconds since epoch.  String form can be RFC2822 or RFC3339 date string
  """
  if(isinstance(date, (int, float))):
    #RFC 3339
    date_string = epoch_to_rfc3339(date)
    #RFC 2822
    #date_string = epoch_to_rfc2822(date)

  elif(isinstance(date, str)):
    # Is it already RFC3339
    try:
      #epoch_time = (datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ") - datetime.datetime(1970, 1, 1)).total_seconds()
      #epoch_time = (datetime.datetime.fromisoformat(date) - datetime.datetime(1970, 1, 1)).total_seconds()
      epoch = datetime.datetime(1970, 1, 1)
      epoch = epoch.replace(tzinfo = datetime.timezone.utc)
      epoch = epoch.astimezone(datetime.timezone.utc)

      epoch_time = (datetime.datetime.fromisoformat(date) - epoch).total_seconds()
      #print("epoch: {}".format(epoch_time))

    except ValueError as rfc3339_error:
      #raise rfc3339_error
      # Nope, not RFC3339

      # Is it an RFC2822 date?
      try:
        date_time_seconds = email.utils.parsedate_to_datetime(date)
        epoch_time = (date_time_seconds - datetime.datetime(1970, 1, 1)).total_seconds()
        #print("epoch: {}".format(epoch_time))

      except Exception as rfc2822_error:
        raise AttributeError("Date string: '{}' not recognized as RFC3339 or RFC2822 formatted date.".format(
          date))

    date_string = epoch_to_rfc3339(epoch_time)

  elif(isinstance(date, datetime.datetime)):
    epoch = datetime.datetime(1970, 1, 1)
    epoch = epoch.replace(tzinfo = datetime.timezone.utc)
    epoch = epoch.astimezone(datetime.timezone.utc)

    #print("date tc: {}".format(date.tzinfo))
    # No time zone, assume UTC
    if(date.tzinfo is None):
      date = date.replace(tzinfo = datetime.timezone.utc)
      #print("date tc: {}".format(date.tzinfo))

    epoch_time = (date - epoch).total_seconds()
    date_string = epoch_to_rfc3339(epoch_time)
  else:
    raise AttributeError("unsupported type: {} value: {} for date".format(type(date), date))

  return(date_string)
