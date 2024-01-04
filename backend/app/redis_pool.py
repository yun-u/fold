import os

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")

pool = redis.ConnectionPool(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
