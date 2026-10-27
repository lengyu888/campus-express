import redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    """惰性创建 Redis 客户端；不可用时返回 None，业务降级运行。"""
    global _client
    if _client is None:
        try:
            client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True,
                socket_connect_timeout=1, socket_timeout=1,
            )
            client.ping()
            _client = client
        except Exception:  # noqa: BLE001
            return None
    return _client
