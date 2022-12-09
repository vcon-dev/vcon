""" Whisper audio transcription filter plugin registration """
import vcon.filter_plugins

# Register the whipser filter plugin
vcon.filter_plugins.FilterPluginRegistry.register("whisper", "vcon.filter_plugins.impl.whisper", "Whisper", "Transcribes dialog recordings")

# Make this the default transcribe type filter plugin
vcon.filter_plugins.FilterPluginRegistry.set_type_default_name("transcribe", "whisper")

