import redis
from .config import config
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)


def check_redis_connection():
    """Check Redis connection by sending a PING command."""
    logger.info(
        f"Checking Redis connection: host={config.REDIS_HOST}, port={config.REDIS_PORT}, db={config.REDIS_DB}"
    )
    try:
        response = redis_client.ping()
        logger.info("Redis PING successful")
        return {
            "status": "success",
            "detail": "Redis connection OK" if response else "Redis PING failed",
        }
    except redis.RedisError as e:
        logger.error(f"Redis connection failed: {str(e)}")
        return {"status": "error", "detail": f"Redis connection failed: {str(e)}"}
