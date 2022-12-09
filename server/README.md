## Setting up redis

We need to run following command.

SADD queue_names "bria-conserver-feed-dev"
SADD queue_names "quiq-conserver-feed-dev"
SADD queue_names "ringplan-conserver-feed-dev"
SADD queue_names "volie-conserver-feed-dev"
SADD active_chains "plugins.call_log"


FT.CREATE idx:adapterIdIndex ON JSON SCHEMA $.attachments[0].adapter AS adapter TAG $.attachments[0].payload.id AS id TAG