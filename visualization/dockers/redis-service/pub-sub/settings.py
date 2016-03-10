import redis

config = {
    'host': '192.168.99.100',
    'port': 6379,
    'db': 0,
}

r = redis.StrictRedis(**config)
