import time
from functools import wraps

def cached(ttl: int = 60):
    store = {}
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in store:
                val, ts = store[key]
                if now - ts < ttl:
                    return val
            val = await func(*args, **kwargs)
            store[key] = (val, now)
            return val
        return wrapper
    return decorator
