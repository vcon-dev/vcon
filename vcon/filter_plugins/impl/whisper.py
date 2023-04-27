#import copy
import os
import sys
import tempfile
import contextlib
import vcon
import vcon.filter_plugins
#import whisper
#import scipy.io.wavfile

logger = vcon.build_logger(__name__)

try:
  import stable_whisper
except Exception as e:
  #patch_url = "https://raw.githubusercontent.com/jianfch/stable-ts/main/stable_whisper.py"
  #print("Please download and install stable_whipser from: {}".format(patch_url))
  cwlogger.info("please install stable_whisper:  \"pip3 install stble-ts\"")
  raise e

class Whisper(vcon.filter_plugins.FilterPlugin):
  """
  PluginFilter to generate transcriptions for a Von
  """
  _supported_media = [ vcon.Vcon.MIMETYPE_AUDIO_WAV ]

  def __init__(self, **options):
    """
    Parameters:
      in_vcon the input Vcon containing dialog recordings

      options (kwargs) - key word arguments containing options for how the transcription
         is to be performed.

         options["model_size"] (str) - model size name (e.g. "tiny", "base") as defined on
           https://github.com/openai/whisper#available-models-and-languages

    Returns:
       copy or modified vcon with transcriptions added

    """
    super().__init__(**options)
    # make model size configurable
    self.whisper_model_size = options.get("model_size", "base")
    logger.info("Initializing whisper model size: {}".format(self.whisper_model_size))
    self.whisper_model = stable_whisper.load_model(self.whisper_model_size)
    #stable_whisper.modify_model(self.whisper_model)

  def filter(self, in_vcon: vcon.Vcon, **options) -> vcon.Vcon:
    """
    Transcribe recording dialogs in given Vcon using the Whisper implementation
`
    Parameters:
      options (kwargs)
        options["whisper"] (dict) are passed through to whisper.Whisper.transcribe
          See help(whisper.DecodingOptions) for pass through options

         options["model_size"] (str) - model size name (e.g. "tiny", "base") as defined on
           https://github.com/openai/whisper#available-models-and-languages

         options["output_types"] List[str] - list of output types to generate.  Current set
           of value supported are:
             "vendor" - add the Whisper specific JSON format transcript as an analysis object
             "word_srt" - add a .srt file with timing on a word or small phrase basis as an analysis object
             "word_ass" - add a .ass file with sentence and highlighted word timeing as an analysis object
           Not specifing "output_type" assumes all of the above will be output, each as a separate analysis object.

    Returns:
      the modified Vcon with added analysis objects for the transcription.
    """
    #TODO do we want to copy the Vcon or modify in placed
    #out_vcon = copy.deepcopy(in_vcon)
    out_vcon = in_vcon
    output_types = options.get("output_options", ["vendor", "word_srt", "word_ass"])
    logger.info("whisper output_types: {}".format(output_types))

    for dialog_index, dialog in enumerate(in_vcon.dialog):
      # TODO assuming none of the dialogs have been transcribed
      #print("dialog keys: {}".format(dialog.keys()))
      if(dialog["type"] == "recording"):
        if(dialog["mimetype"] in self._supported_media):
          # If inline or externally referenced recording:
          if(any(key in dialog for key in("body", "url"))):
            if("body" in dialog and dialog["body"] is not None and dialog["body"] != ""):
              # Need to base64url decode recording
              body_bytes = in_vcon.decode_dialog_inline_body(dialog_index)
            elif("url" in dialog and dialog["url"] is not None and dialog["url"] != ""):
              # HTTP GET and verify the externally referenced recording
              body_bytes = in_vcon.get_dialog_external_recording(dialog_index)
            else:
              raise Exception("recording type dialog[{}] has no body or url.  Should not have gotten here.".format(dialog_index))

            with tempfile.TemporaryDirectory() as temp_dir:
              transcript = None
              with tempfile.NamedTemporaryFile(prefix= temp_dir + os.sep, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(body_bytes)
                #rate, samples = scipy.io.wavfile.read(body_io)
                # ts_num=7 is num of timestamps to get, so 7 is more than the default of 5
                # stab=True  is disable stabilization so you can do it later with different settings
                #transcript = self.whisper_model.transcribe(samples, ts_num=7, stab=False)

                # whisper has some print statements that we want to go to stderr
                with contextlib.redirect_stdout(sys.stderr):
                  whisper_options = options.get("whisper", {})
                  if(options.get("model_size", self.whisper_model_size) == self.whisper_model_size):
                    model = self.whisper_model
                  else:
                    raise Exception("Not implemented whisper model initialized with size: {} transcribe requested for size: {}".format(
                      self.whisper_model_size, options["model_size"]))
                    # TODO generate a one time use model for the requested size

                  transcript = model.transcribe(temp_audio_file.name, **whisper_options)
                  # dict_keys(['text', 'segments', 'language'])
              # aggressive allows more variation
              #stabilized_segments = stable_whisper.stabilize_timestamps(transcript["segments"], aggressive=True)
              #transcript["segments"] = stabilized_segments
              # stable_segments = stable_whisper.stabilize_timestamps(transcript, top_focus=True)
              # transcript["stable_segments"] = stable_segments

              # need to add transcription to dialog.analysis
              if("vendor" in output_types):
                out_vcon.add_analysis_transcript(dialog_index, transcript, "Whisper", "whisper_word_timestamps")

              if("word_srt" in output_types):
                with tempfile.NamedTemporaryFile(prefix= temp_dir + os.sep, suffix=".srt") as temp_srt_file:
                  # stable_whisper has some print statements that we want to go to stderr
                  with contextlib.redirect_stdout(sys.stderr):
                    stable_whisper.results_to_word_srt(transcript, temp_srt_file.name)
                  srt_bytes = temp_srt_file.read()
                  out_vcon.add_analysis_transcript(dialog_index, srt_bytes.decode("utf-8"), "Whisper", "whisper_word_srt", encoding = "none")

              if("word_ass" in output_types):
                with tempfile.NamedTemporaryFile(prefix= temp_dir + os.sep, suffix=".ass") as temp_ass_file:
                  stable_whisper.results_to_sentence_word_ass(transcript, temp_ass_file.name)
                  ass_bytes = temp_ass_file.read()
                  out_vcon.add_analysis_transcript(dialog_index, ass_bytes.decode("utf-8"), "Whisper", "whisper_word_ass", encoding = "none")

          else:
            pass # ignore??

        else:
          print("unsupported media type: {} in dialog[{}], skipped whisper transcription".format(dialog.mimetype, dialog_index))

    return(out_vcon)

