import redis
import os

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379)

def publish_message(user, message):
    r.publish("chat_channel", f"{user}: {message}")
