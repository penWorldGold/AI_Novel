# api_rate_limiter.py
import time
import logging
from collections import deque
import threading


class APIRateLimiter:
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        self.call_history = deque()
        self.api_limits = {
            "DeepSeek": {"free": 3, "paid": 60},
            "Kimi": {"free": 5, "paid": 60}
        }

    def get_rate_limit(self):
        engine = self.config.get('global', 'api_engine', 'DeepSeek')
        plan = self.config.get('global', 'api_plan', 'free')
        return self.api_limits.get(engine, {}).get(plan, 3)

    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            rate_limit = self.get_rate_limit()
            while self.call_history and current_time - self.call_history[0] > 60:
                self.call_history.popleft()
            if len(self.call_history) >= rate_limit:
                oldest_call = self.call_history[0]
                wait_time = 60 - (current_time - oldest_call) + 1
                self.logger.warning(f"API速率限制，等待 {wait_time:.1f} 秒...")
                time.sleep(wait_time)
                current_time = time.time()
            self.call_history.append(current_time)