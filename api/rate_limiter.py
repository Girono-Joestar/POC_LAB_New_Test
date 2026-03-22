import time
import threading
import logging

logger = logging.getLogger("poc_ai_lab.rate_limiter")

class RateLimiter:
    """
    Simple thread-safe rate limiter to enforce a maximum number of requests per minute.
    Default is 30 RPM (one request every 2 seconds).
    """
    def __init__(self, rpm=30):
        self.interval = 60.0 / rpm
        self.last_call = 0.0
        self.lock = threading.Lock()
        logger.info("🕒 RateLimiter initialized with %d RPM (interval: %.2fs)", rpm, self.interval)

    def wait(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                logger.debug("⏳ Rate limiting: sleeping for %.2fs", sleep_time)
                time.sleep(sleep_time)
            self.last_call = time.time()

# Global instances for LLM and Embeddings
llm_limiter = RateLimiter(rpm=30)
embed_limiter = RateLimiter(rpm=30)
