# config_manager.py
import json
import os
import configparser
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_path='novel_analyzer_config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser(interpolation=None)
        self.defaults = {
            'global': {
                'novel_path': '',
                'output_dir': 'output',
                'api_engine': 'DeepSeek',
                'api_key': '',
                'api_plan': 'free'
            },
            'chapter_split': {
                'regex': r'第[零一二三四五六七八九十百千0-9]+章',
                'encoding': 'auto'
            },
            'stage1': {
                'chapter_range': 'all',
                'term_binding': 'true',
                'prompt': """# 角色：小说分析师..."""
            },
            'stage2': {
                'block_sensitivity': 'medium',
                'cross_volume': 'false',
                'prompt': """# 角色：分块分析师..."""
            },
            'stage3': {
                'foreshadow_depth': '2',
                'prompt': """# 角色：情节分析师..."""
            },
            'stage4': {
                'climax_threshold': '4',
                'prompt': """# 角色：大纲分析师..."""
            },
            'visualization': {
                'layout_style': 'circular'
            }
        }

        if os.path.exists(config_path):
            self.config.read(config_path, encoding='utf-8')
        else:
            self._create_default_config()

    def _create_default_config(self):
        for section, options in self.defaults.items():
            self.config[section] = options
        self.save_config()

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get(self, section, option, fallback=None):
        try:
            return self.config.get(section, option)
        except:
            return self.defaults.get(section, {}).get(option, fallback)

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def load_terminology(self):
        output_dir = self.get('global', 'output_dir', 'output')
        term_path = os.path.join(output_dir, 'terminology.json')
        if os.path.exists(term_path):
            try:
                with open(term_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def update_terminology(self, new_terms):
        output_dir = self.get('global', 'output_dir', 'output')
        term_path = os.path.join(output_dir, 'terminology.json')
        current_terms = self.load_terminology()
        current_terms.update(new_terms)

        os.makedirs(os.path.dirname(term_path), exist_ok=True)
        with open(term_path, 'w', encoding='utf-8') as f:
            json.dump(current_terms, f, ensure_ascii=False, indent=2)
        return current_terms