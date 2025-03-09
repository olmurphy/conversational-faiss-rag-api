# src/infrastructure/health_checks.py
import asyncio
import logging
from configurations.redis_config import RedisConfig  # Import RedisConfig from the same directory

async def redis_health_check_task(redis_config: RedisConfig, interval: int = 60):
    """Periodically checks Redis health."""
    logger = logging.getLogger(__name__) #get a logger in the file.
    while True:
        if not redis_config.check_health():
            logger.error("Redis health check failed!")
            # Implement your alert/restart/failover logic here
            # Example:
            # send_alert("Redis connection failed")
            # attempt_redis_restart()
            # switch_to_backup_redis()
        else:
            logger.debug("Redis health check successful")
        await asyncio.sleep(interval)

# Example alert function
def send_alert(message: str):
    # Implement your alerting logic (e.g., send an email, Slack message)
    print(f"ALERT: {message}")

# Example restart function
def attempt_redis_restart():
    # Implement logic to restart Redis (e.g., using subprocess)
    print("Attempting Redis restart...")

# Example failover function
def switch_to_backup_redis():
    # Implement logic to switch to a backup Redis server
    print("Switching to backup Redis...")