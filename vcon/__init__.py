"""
Module for creating and modifying vCon conversation containers.
see https:/vcon.dev
"""
import typing
import json
import jose.utils

class UnsupportedVconVersion(Exception):
  """ Thrown if vcon version string is not of set of versions supported by this package"""

class VconDictList:
  """ descriptor for Lists of dicts in vcon """
  def __set_name__(self, owner_class, name):
    #print("defining new VconList: {}".format(name))
    self.name = name

  def __get__(self, instance_object, class_type = None) -> list:
    #print("getting: {} inst type: {} class type: {}".format(self.name, type(instance_object), type(class_type)))
    # TODO: once signed, this should return a read only list
    return(instance_object._vcon_dict.get(self.name, None))

  def __set__(self, instance_object, value : dict) -> None:
    raise AttributeError("not allowed to replace {} List".format(self.name))

class Vcon():
  """
  Constructor, Serializer and Deserializer for vCon conversation data container.

  Attributes:
    parties (List[dict]): containing information on each party to the conversation
    dialog (List[dict]): containing information dialog exchanges (text or audio/video recordings)
    analysis (List[dict]): containing analysis information on the dialog
    attachments (List[dict]): containing meta data about as well as the documents exchanged during the conversation

  """
  VCON_VERSION = "vcon"
  PARTIES = "parties"
  DIALOG = "dialog"
  ANALYSIS = "analysis"
  ATTACHMENTS = "attachments"

  parties = VconDictList()
  dialog = VconDictList()
  analysis = VconDictList()
  attachments = VconDictList()

  def __init__(self):
    self._vcon_dict = {}
    self._vcon_dict[Vcon.VCON_VERSION] = "0.0.1"
    self._vcon_dict[Vcon.PARTIES] = []
    self._vcon_dict[Vcon.DIALOG] = []
    self._vcon_dict[Vcon.ANALYSIS] = []
    self._vcon_dict[Vcon.ATTACHMENTS] = []

  def __add_new_party(self, index : int) -> int:
    """
    check if a new party needs to be added to the list

    Parameters:
    index (int): -1 indicates adding a new party, positive numbers
          throw AttributeError if the party with that index does not already exist

    Returns:
      party index in the list
    """
    party = index
    if(party == -1):
      self._vcon_dict[Vcon.PARTIES].append({})
      party = len(self._vcon_dict[Vcon.PARTIES]) - 1

    else:
      if(not len(self._vcon_dict[Vcon.PARTIES]) > index):
        raise AttributeError(
          "index: {} > then party List length: {}.  Use index of -1 to add one to the end.".format(
          index, len(self._vcon_dict[Vcon.PARTIES])))

    return(party)

  def get_conversation_time(self) -> typing.Tuple[str, float]:
    """
    Get the start time and duration of the vcon

    Parameters: none

    Returns:
      Tuple(str, float): RFC2822 format string start time and float duration in seconds
    """
    # TODO: loop through dialogs and find the oldest start time, calculate end time from
    # duration, find the most recent end time and return the results
    raise Exception("not implemented")

  def set_party_tel_url(self, tel_url : str, party_index : int =-1) -> int:
    """
    Set tel URL for a party.

    Parameters:
    tel_url
    party_index (int): index of party to set tel url on
                  (-1 indicates a new party should be added)

    Returns:
    int: if success, opsitive int index of party in list
    """

    # TODO: should label as caller or called

    party_index = self.__add_new_party(party_index)

    self._vcon_dict[Vcon.PARTIES][party_index]['tel'] = tel_url

    return(party_index)

  def add_dialog_inline_recording(self, body : bytes,
    start_time : typing.Union[str, int, float],
    duration : typing.Union[int, float],
    parties : typing.Union[int, typing.List[int], typing.List[typing.List[int]]],
    mime_type : str,
    file_name : str = None) -> int:
    """
    Add a recording of a portion of the conversation, inline (base64 encoded) to the dialog.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    duration (int or float): duration of the recording in seconds
    parties (int, List[int], List[List[int]]): party indices speaking in each
               channel of the recording.
    mime_type (str): mime type of the recording
    file_name (str): file name of the recording (optional)

    Returns:
            Number of bytes read from body.
    """
    # TODO: do we want to know the number of channels?  e.g. to verify party list length

    # TODO: should we validate the start time?

    new_dialog = {}
    new_dialog['type'] = "recording"
    new_dialog['start'] = start_time
    new_dialog['duration'] = duration
    new_dialog['parties'] = parties
    new_dialog['mimetype'] = mime_type
    if(file_name is not None):
      new_dialog['filename'] = file_name

    new_dialog['encoding'] = "base64url"
    encoded_body = jose.utils.base64url_encode(body).decode('utf-8')
    #print("encoded body type: {}".format(type(encoded_body)))
    new_dialog['body'] = encoded_body

    self._vcon_dict[Vcon.DIALOG].append(new_dialog)


    return(len(body))

  def decode_dialog_inline_recording(self, dialog_index):
    dialog = self.dialog[dialog_index]
    if(dialog["type"] != "recording"):
      raise AttributeError("dialog[{}] is not a recording file")
    if(dialog.get("body") is None):
      raise AttributeError("dialog[{}] does not contain an inline recording file")

    # This is wrong.  decode should take a string not bytes, but it fails without the bytes conversion
    # this is a bug in jose.baseurl_decode
    decoded_body = jose.utils.base64url_decode(bytes(dialog["body"], 'utf-8'))

    return(decoded_body)

  def add_dialog_external_recording(self, body : bytes,
    start_time : typing.Union[str, int, float],
    duration : typing.Union[int, float],
    parties : typing.Union[int, typing.List[int], typing.List[typing.List[int]]],
    external_url: str,
    mime_type : str =None,
    file_name : str =None) -> int:
    """
    Add a recording of a portion of the conversation, as a reference via the given
    URL, to the dialog and generate a signature and key for the content.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    duration (int or float): duration of the recording in seconds
    parties (int, List[int], List[List[int]]): party indices speaking in each
               channel of the recording.
    external_url (string): https URL where the body is stored securely
    mime_type (str): mime type of the recording (optional)
    file_name (str): file name of the recording (optional)

    Returns:
            Number of bytes read from body.
    """

    return(-1)

  def dumps(self) -> str:
    """
    Dump the vCon as a JSON string.

    Parameters: none
    Returns:
             String containing JSON representation of the vCon.
    """

    # TODO: Should it throw an acception if its not signed?  Could have argument to
    # not throw if it not signed.

    return(json.dumps(self._vcon_dict))

  def loads(self, vcon_json : str) -> None:
    """
    Load the vCon from a JSON string.
    Assumes that this vCon is an empty vCon as it is not cleared.

    Parameters:
      vcon_json (str): string containing JSON representation of a vCon

    Returns: none
    """

    #TODO: Should check unsafe stuff is not loaded

    #TODO: Once signing is supported, this will get more complicated as
    #      we will need to check the format as to whether it is signed or
    #      not and deconstruct the loaded object.

    vcon_dict = json.loads(vcon_json)

    # validate version
    version_string = vcon_dict.get('vcon', "not set")
    if(version_string != "0.0.1"):
      raise UnsupportedVconVersion("loads of JSON vcon version: \"{}\" not supported".format(version_string))

    self._vcon_dict = vcon_dict

