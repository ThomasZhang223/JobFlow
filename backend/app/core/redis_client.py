import asyncio
import json
from redis.asyncio import Redis
from typing import Callable, Awaitable

from app.core.config import settings

# Type alias: handler function that receives raw dict, returns None when awaited
# Handler for async client methods, message recieved is passed to handler
MessageHandler = Callable[[dict], Awaitable[None]]

class RedisClient:
    """
    Async Redis client defintion for pub/sub messages
    Validation and handler function defined in main for API
    """

    def __init__(self):
        # Build TCP connection URL for pub/sub (REST API doesn't support pub/sub)
        self.url = f"rediss://:{settings.upstash_redis_rest_token}@{settings.upstash_redis_rest_url[8:]}:{settings.upstash_redis_port}?ssl_cert_reqs=required"
        self.redis = None
        self.pubsub = None
        self.subscriber_task = None

    async def connect(self):
        try:
            self.redis = Redis.from_url(self.url)
            await self.redis.ping()
            print(f'Redis connection success (TCP) \n')

        except Exception as e:
            print(f"Redis Connection failed: {e}")
            self.redis = None
        
    async def disconnect(self):
        if self.subscriber_task:
            # Task, use .cancel
            # .cancle only sends a cancellation request, await for task to finish
            self.subscriber_task.cancel()
            try: # handles any errors from private internal listener function
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
        
        # Using redis.asyncio, so await their close(async method)
        if self.pubsub:
            await self.pubsub.close()
            
        if self.redis:
            await self.redis.close()
            
    async def subscribe(self, channel: str, handler: MessageHandler):
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(channel)
        # Create new async task to prevent liste loop from blocking program flow
        self.subscriber_task = asyncio.create_task(self._listener(handler))
        
    async def _listener(self, handler: MessageHandler):
        try: 
            while True:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True, # Redis automatically sends out a subscribe message; ignore
                    timeout=1.0 # System will wait for one second to attempt to read
                    )
                if message and message['type'] == 'message':
                    data = message['data'].decode("utf-8")
                    parsed = json.loads(data)
                    await handler(parsed) # Sends dict data to validation in main               
        except asyncio.CancelledError:
            raise # Propogates to disconnect

redis_client = RedisClient()