# api_handler.py
import time
import requests
import logging
from http import HTTPStatus
from config_manager import ConfigManager
from api_rate_limiter import APIRateLimiter


class APIHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.engine = self.config.get('global', 'api_engine')
        self.api_key = self.config.get('global', 'api_key')
        self.base_url = self._get_base_url()
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = APIRateLimiter(config_manager)

    def _get_base_url(self):
        if self.engine == 'DeepSeek':
            return "https://api.deepseek.com/v1/chat/completions"
        elif self.engine == 'Kimi':
            return "https://api.moonshot.cn/v1/chat/completions"
        else:
            raise ValueError(f"Unsupported API engine: {self.engine}")

    def generate(self, prompt, max_retries=5):
        if not self.api_key:
            raise ValueError("API密钥未配置")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "deepseek-chat" if self.engine == "DeepSeek" else "moonshot-v1-32k",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4000
        }

        for attempt in range(max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                response = requests.post(self.base_url, json=payload, headers=headers, timeout=120)

                if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    retry_after = response.headers.get('Retry-After', 30)
                    wait_time = max(int(retry_after), 30)
                    self.logger.warning(f"API限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    continue
                wait_time = min(2 ** attempt, 60)
                self.logger.error(f"HTTP错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(wait_time)
            except Exception as e:
                wait_time = min(2 ** attempt, 30)
                self.logger.error(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(wait_time)

        raise Exception(f"API调用失败，已达最大重试次数 {max_retries}")

    def batch_generate(self, prompts, batch_size=5):
        results = []
        total = len(prompts)
        for i in range(0, total, batch_size):
            batch = prompts[i:i + batch_size]
            for j, prompt in enumerate(batch):
                try:
                    results.append(self.generate(prompt))
                    self.logger.info(f"API请求完成: {i + j + 1}/{total}")
                except Exception as e:
                    self.logger.error(f"API请求失败: {str(e)}")
                    results.append(None)
            time.sleep(1)
        return results