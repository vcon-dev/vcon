import boto3
import logging
import logging.config
import asyncio

logger = logging.getLogger(__name__)

from settings import AWS_KEY_ID, AWS_SECRET_KEY


sqs = boto3.resource(
    "sqs",
    region_name="us-east-1",
    aws_access_key_id=AWS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY,
)

def receive_messages(queue, max_number_of_messages, wait_time_seconds):
    return queue.receive_messages(MaxNumberOfMessages=max_number_of_messages, WaitTimeSeconds=wait_time_seconds)


async def listen_to_sqs(queue_name: str):
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    loop = asyncio.get_running_loop()
    while True:
        messages = await loop.run_in_executor(None, receive_messages, queue, 10, 15);
        for message in messages:
            yield message
