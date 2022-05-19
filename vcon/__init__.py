import typing
import json
#import jose.utils

class UnsupportedVconVersion(Exception):
  pass

class vcon():
  """
  Constructor, Serializer and Deserializer for vCon conversation data container.

  Attributes:
    None public`
  """
  def __init__(self):
    self._vcon_dict = {}
    self._vcon_dict["vcon"] = "0.0.1"
    self._vcon_dict["participants"] = []
    self._vcon_dict["dialog"] = []
    self._vcon_dict["analysis"] = []
    self._vcon_dict["attachments"] = []

  def add_new_participant(self, index : int) -> int:
    participant = index
    if(participant == -1):
      self._vcon_dict["participants"].append({})
      participant = len(self._vcon_dict["participants"]) - 1

    else:
      if(not len(self._vcon_dict["participants"]) > index):
        raise AttributeError("index: {} > then participant List length: {}.  Use index of -1 to add one to the end.".format(index, len(self._vcon_dict["participants"])))
      
    return(participant)

  def set_party_tel_url(self, tel_url : str, participant : int =-1) -> int:
    """
    Set tel URL for a participant.
  
    Parameters:
    tel_url
    participant (int): index of participant to set tel url on
                  (-1 indicates a new participant should be added)
  
    Returns:
    int: if success, opsitive int index of participant in list
    """

    participant = self.add_new_participant(participant)

    self._vcon_dict["participants"][participant]['tel'] = tel_url
    
    return(participant)

  def set_party_join_time(self, joined_time : typing.Union[str, int, float], participant : int = -1) -> int:
    """
      Set the time that a participant joined the conversation.  Update the vCon start if
      it is not set or after the join time for the participant.
  
    Parameters:
    joined_time (str, int, float): string containing RFC 2822 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    participant (int): index of participant to set joined time on
                  (-1 indicates a new participant should be added)
  
    Returns: 
      participant index
    """

    # TODO: should we have a global vCon start and stop as a convenience or just label 
    # start and stop/duration for each participant?

    # TODO: what about a party that joins and leaves multiple times?  Should participant have
    # array of join and leave times?

    # TODO: do we store leave time or duration?  

    # TODO: should validate joined time

    participant = self.add_new_participant(participant)

    self._vcon_dict["participants"][participant]['joined'] = joined_time
    
    return(participant)

  def add_dialog_inline_recording(self, body : bytes, start_time : typing.Union[str, int, float], 
    paticipants : typing.Union[int, typing.List[int], typing.List[typing.List[int]]], 
    mime_type : str, file_name : str = None) -> int:
    """
    Add a recording of a portion of the conversation, inline (base64 encoded) to the dialog.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    participants (int, List[int], List[List[int]]): participant indices speaking in each
               channel of the recording.
    mime_type (str): mime type of the recording
    file_name (str): file name of the recording (optional)
  
    Returns:
            Number of bytes read from body.
    """
    # TODO: do we want to know the number of channels?  e.g. to verify participant list length

    new_dialog = {}
    new_dialog['type'] = "recording"
    new_dialog['start'] = start_time
    new_dialog['participants'] = participants
    new_dialog['mimetype'] = mime_type
    if(file_name != None):
      new_dialog['filename'] = file_name
    
    
    new_dialog['encoding'] = "base64url"
    encoded_body = jose.utils.base64url_encode(body)
    new_dialog['body'] = encoded_body

    return(len(body))

  def add_dialog_external_recording(self, body : bytes, start_time : typing.Union[str, int, float], 
    paticipants : typing.Union[int, typing.List[int], typing.List[typing.List[int]]], 
    external_url: str, mime_type : str =None, file_name : str =None) -> int:
    """
    Add a recording of a portion of the conversation, as a reference via the given
    URL, to the dialog and generate a signature and key for the content.

    Parameters:
    body (bytes): bytes for the audio or video recording (e.g. wave or MP3 file).
    start_time (str, int, float): Date, time of the start of the recording.
               string containing RFC 2822 date time stamp or int/float
               containing epoch time (since 1970) in seconds.
    participants (int, List[int], List[List[int]]): participant indices speaking in each
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

