# analyzers/base_analyzer.py
import logging
from api_handler import APIHandler
from config_manager import ConfigManager
from file_processor import FileProcessor
import threading


class BaseAnalyzer:
    def __init__(self, config_manager):
        self.config = config_manager
        self.api_handler = APIHandler(config_manager)
        self.file_processor = FileProcessor
        self.logger = logging.getLogger(self.__class__.__name__)
        self.progress_callback = None
        self.pause_event = None
        self.stop_event = None

    def set_control_events(self, pause_event, stop_event):
        self.pause_event = pause_event
        self.stop_event = stop_event

    def check_pause(self):
        if self.pause_event and self.pause_event.is_set():
            self.logger.info("任务已暂停")
            while self.pause_event.is_set():
                if self.stop_event and self.stop_event.is_set():
                    self.logger.info("任务停止请求，取消暂停等待")
                    return False
                threading.Event().wait(0.5)
            self.logger.info("任务继续")
        return True

    def check_stop(self):
        if self.stop_event and self.stop_event.is_set():
            self.logger.info("任务停止请求")
            return True
        return False

    def get_output_dir(self):
        return self.config.get('global', 'output_dir', 'output')

    def get_chapter_range(self, range_str='all'):
        if range_str.lower() == 'all':
            return None

        chapters = set()
        parts = range_str.split(',')
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                chapters.update(range(int(start), int(end) + 1))
            else:
                chapters.add(int(part))
        return sorted(chapters)

    def update_progress(self, current, total, message=None):
        if self.progress_callback:
            progress = (current / total) * 100 if total > 0 else 0
            self.progress_callback(progress, message)
            if message:
                self.logger.info(message)