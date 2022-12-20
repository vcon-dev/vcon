# Plugins

Plugins are components that take a vCon UUID as an input, transforms the vCon, then publishes
that vCon UUID to a set of REDIS channels.  As an example, a transcription plugin would 
accept a vCon UUID as an input, look for audio conversations, transcribe each one, and add
those transcriptions as analysis.  Because plugins have a regular interface of both vCon 
input and output, you can "chain" them together to create a pipeline of plugins.  In order
to filter out a vCon from a chain, the plugin won't output that vCon UUID, effectively
ending its processing.

It does not matter how long a plugin takes to process.  Sometimes, external services
might take a long time to complete their operation. The plugin will keep that vCon
as long as the processing takes, and publish the UUID when complete.

## Flow

    - Receive the UUID of an existing vCon published on a REDIS channel
    - Optionally, read that vCon into memory from redis
    - Do some work on it
    - Modify the vCon if appropriate, and save it back in REDIS
    - Send it to the next plugin (optional) by publishing the vCon UUID to one or more REDIS channels. If 
    the plugin does not wish to forward this vCon to the next plugin, it would not publish the UUID.


## Examples of plugins are:
- a transcript plugin that looks for audio, then transcribes it and adds a new 
analysis block
- a summary plugin that looks for audio, and creates a short paragraph describing it,
adding it in as a analysis block
- a stitcher plugin that looks for incomplete information in the parties section
of a vCon, and fills in the missing data from third party systems
- a storage plugin (described elsewhere) that takes every inbound vCon and stores
it in a file system, a database or S3
- a customer journey plugin that looks for a sales lead that was the reason for the call
in the first place, and adds that sales lead as an attachment.
