# Adapters 
Adapters connect outside communications services, like softphones and dialers, into the conserver. The conserver
takes these events and creates vCons out of them, stores them in a REDIS key, then publishes the UUID of the vCon
into a REDIS based PUB/SUB channel.

Sometimes we will get updates from a service after a call is ended, and a vCon made.  For instance, 
the recording of a call may appear minutes after a call completed event. In this example, when we 
received the call_completed event, we created a vCon and published the UUID.  When the recording 
event arrives, instead of remembering the original vCon UUID or searching for it, we choose to make
a new vCon that contains this recording, resulting in two vCons that refer to the same call, with two 
different IDs.  In order to merge them, a plugin should be used downstream to look for these second vCons, 
take the information from them and merge it with the original. 

An adapter has the following responisbilities: 
- To convert the raw event information into as much of a vCon as it can.
- Clean the incoming data for data integrity. For example, 5085551212 might be converted by the adapter into "+15083649972"
- To store the vCon into a REDIS key with a name based on the UUID of the vCon. 
- Publish the UUID of the vCon into one or more REDIS channels.  

There are a number of possible ways for raw events to 

### Flow
    - Receive raw event data. This data can arrive in a number of ways, either from messaging busses, 
    or HTTP posts, or new files in an S3 bucket.  
    - Create a new vCon based on the event data, cleaning whatever data it can. 
    - Save the new vCon in REDIS using the UUID of the vCon as the REDIS key (vcon:23423-23423-234234-234)
    - Publish the UUID of the vCon into one or more REDIS channels. By convention, new vCons are published
    to the "ingress-vcons" channel, but this is only a default. 


### Examples of plugins are:
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

### Flow

    - Receive the UUID of an existing vCon published on a REDIS channel
    - Optionally, read that vCon into memory from redis
    - Do some work on it
    - Modify the vCon if appropriate, and save it back in REDIS
    - Send it to the next plugin (optional) by publishing the vCon UUID to one or more REDIS channels. If 
    the plugin does not wish to forward this vCon to the next plugin, it would not publish the UUID.


### Examples of plugins are:
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


# Storage


# Setting up redis

We need to run following command.

SADD queue_names "quiq-conserver-feed-dev"
SADD queue_names "ringplan-conserver-feed-dev"
SADD queue_names "volie-conserver-feed-dev"
SADD active_chains "plugins.call_log"


FT.CREATE idx:adapterIdIndex ON JSON SCHEMA $.attachments[0].adapter AS adapter TAG $.attachments[0].payload.id AS id TAG


FT.CREATE idx:adapterIdsIndex ON JSON SCHEMA $.attachments[0:].adapter AS adapter TAG $.attachments[0:].payload.id AS id TAG
