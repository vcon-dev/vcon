from lib.logging_utils import init_logger
from redis_mgr import get_key, set_key, get_client
import requests
import random
import asyncio
from settings import LEADER_TICK_INTERVAL_S, LEADER_URL, LEADER_TOKEN, LEADER_VCON_PERCENTAGE, LEADER_EXPIRES_S, LEADER_INGRESS_LISTS
import aiohttp

# If the leader server is defined, then we need to start the follower adapter.
logger = init_logger("follower_adapter")
logger.info("Loaded follower adapter...")

continue_loop = True

class Adapter:
    def __init__(self, config):
        self.config = config
        self.logger = init_logger("follower_adapter")
        self.logger.info("Loaded follower adapter...")
        self.poll_interval_s = self.config.get("poll_interval_s", LEADER_TICK_INTERVAL_S)
        self.percent_content = self.config.get("percent_content", LEADER_VCON_PERCENTAGE)
        self.vcon_expires_s = self.config.get("vcon_expires_s", LEADER_EXPIRES_S)
        self.ingress_lists = self.config.get("ingress_lists", LEADER_INGRESS_LISTS)
        self.leader_url = self.config.get("leader_url", LEADER_URL)
        self.leader_token = self.config.get("leader_token", LEADER_TOKEN)

    async def start(self):
        global continue_loop
        continue_loop = True
        await asyncio.create_task(self.check_for_new_events())
        self.logger.info("Started follower adapter")
 
    def stop(self):
        global continue_loop
        continue_loop = False
        self.logger.info("Stopping follower adapter")

    async def check_for_new_events(self):
        global continue_loop

        self.logger.info("Starting follower adapter")
        redis = await get_client()  # Get a connection to the Redis server
        self.logger.info("Connected to Redis")

        while continue_loop:
            logger.info("Checking for new vcons...")

            # Using HTTP GET to get the latest vcons from the server, authorized with an API key
            # and process them. The API key is passed in the Authorization header.
            try:
                response = requests.get(f"{self.leader_url}/vcon", headers={"Authorization": "Bearer " + self.leader_token})
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                logger.info(f"Error connecting to leader server: {e}")
                await asyncio.sleep(self.poll_interval_s)
                continue

            # The list of vcon IDs is returned as a JSON array, so we can iterate over it
            # and process each vcon. The vcon is stored in Redis and pushed onto each list.

            # There's a chance that we are not polling fast enough, and we could miss some vcons.
            # To detect this situation, we could use the "since" parameter in the GET request.
            # This would allow us to get all vcons since the last one we received. However, this

            redis = get_client()  # Get a connection to the Redis server
            for vcon_id in response.json():
                logger.debug(f"Received vcon: {vcon_id}")

                # First, let's check to see if we already have this vcon
                # in the Redis server. If we do, we can skip it.            
                if await redis.exists("vcon:" + vcon_id):
                    logger.debug(f"Vcon {vcon_id} already exists in Redis")
                    continue

                # We don't have this vcon, if we aren't 100% downsyncing, we need to
                # check to see if we should skip it.
                if random.random() > float(self.percent_content):
                    logger.debug(f"Skipping vcon {vcon_id}")
                    continue
                # Get the vcon from the server

                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.leader_url}/vcon/{vcon_id}", headers={"Authorization": "Bearer " + self.leader_token }) as response:
                        vcon = await response.json()

                        # Add the vcon to the Redis server
                        await set_key("vcon:" + vcon_id, vcon)

                        # Set the expiration time for the vcon
                        await redis.expire("vcon:" + vcon_id, self.vcon_expires_s)
                        logger.info(f"Added vcon {vcon_id} to Redis")

                        # Push the vcon onto each list
                        for list_name in self.ingress_lists:
                            await redis.lpush(list_name, vcon_id)
                            logger.info(f"Added vcon {vcon_id} to list {list_name}")

            # Sleep for the poll interval
            await asyncio.sleep(self.poll_interval_s) 


