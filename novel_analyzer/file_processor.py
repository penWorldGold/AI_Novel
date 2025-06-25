# file_processor.py
import os
import re
import json
import pandas as pd
import chardet
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class FileProcessor:
    progress_callback = None

    @staticmethod
    def detect_encoding(file_path):
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'

    @staticmethod
    def advanced_detect_encoding(file_path):
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            bom_dict = {
                b'\xff\xfe': 'utf-16',
                b'\xfe\xff': 'utf-16-be',
                b'\xff\xfe\x00\x00': 'utf-32',
                b'\x00\x00\xfe\xff': 'utf-32-be'
            }
            for bom, encoding in bom_dict.items():
                if raw_data.startswith(bom):
                    return encoding
            result = chardet.detect(raw_data)
            if result['confidence'] > 0.85:
                return result['encoding']
            if b'\xb0\xa1' in raw_data:
                return 'gbk'
            if b'\xa4\x40' in raw_data:
                return 'big5'
            try:
                raw_data.decode('utf-8')
                return 'utf-8'
            except:
                return 'latin1'

    @staticmethod
    def create_output_structure(output_dir):
        dirs = [
            'chapters',
            'stage1_summaries',
            'stage2_blocks',
            'stage3_plots',
            'stage4_outline'
        ]
        for d in dirs:
            os.makedirs(os.path.join(output_dir, d), exist_ok=True)
        term_path = os.path.join(output_dir, 'terminology.json')
        if not os.path.exists(term_path):
            with open(term_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    @staticmethod
    def split_chapters(novel_path, output_dir, chapter_regex=r'第[零一二三四五六七八九十百千0-9]+章', encoding='auto'):
        encodings_to_try = ['utf-8', 'gb18030', 'gbk', 'big5', 'latin1']
        content = None

        try:
            if encoding != 'auto':
                try:
                    with open(novel_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"使用手动指定编码: {encoding}")
                except Exception as e:
                    logger.warning(f"手动编码 {encoding} 失败: {str(e)}")
                    encoding = 'auto'

            if encoding == 'auto':
                logger.info("开始自动检测文件编码...")
                for encoding in encodings_to_try:
                    try:
                        with open(novel_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        logger.info(f"成功使用编码: {encoding}")
                        break
                    except UnicodeDecodeError as e:
                        error_position = e.args[2]
                        context_start = max(0, error_position - 20)
                        context_end = min(len(content) if content else 0, error_position + 20)
                        context = content[context_start:context_end] if content else ""
                        logger.warning(f"编码 {encoding} 失败: {str(e)}")
                        logger.warning(f"错误位置: {error_position}, 上下文: {context}")
                        continue
                    except Exception as e:
                        logger.error(f"文件读取异常: {str(e)}")
                        continue

            if content is None:
                logger.warning("标准编码尝试失败，使用高级编码检测")
                try:
                    encoding = FileProcessor.advanced_detect_encoding(novel_path)
                    logger.info(f"高级检测建议编码: {encoding}")
                    with open(novel_path, 'r', encoding=encoding) as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"高级编码检测失败: {str(e)}")

            if content is None:
                logger.error("所有编码尝试失败，使用二进制模式读取并忽略错误")
                try:
                    with open(novel_path, 'rb') as f:
                        binary_data = f.read()
                    detected = chardet.detect(binary_data)
                    if detected['confidence'] > 0.7:
                        encoding = detected['encoding']
                        logger.info(f"二进制检测编码: {encoding}")
                        content = binary_data.decode(encoding, errors='ignore')
                    else:
                        content = binary_data.decode('utf-8', errors='ignore')
                        logger.warning("使用utf-8并忽略解码错误")
                except Exception as e:
                    logger.critical(f"最终文件读取失败: {str(e)}")
                    return []
        except PermissionError as e:
            logger.error(f"文件权限被拒绝: {novel_path} - 请检查文件是否被其他程序占用")
            logger.error(f"详细错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"文件处理异常: {str(e)}")
            return []

        if content.startswith('\ufeff'):
            content = content[1:]
            logger.info("移除UTF-8 BOM头")
        content = content.encode('utf-8', 'replace').decode('utf-8')

        lines = content.split('\n')
        pattern = re.compile(chapter_regex)
        chapters = []
        current_chapter = []
        chapter_title = ""
        chapter_num = 1
        chapter_title_counts = defaultdict(int)
        skip_preface = True

        for i, line in enumerate(lines):
            if skip_preface:
                if pattern.match(line.strip()):
                    skip_preface = False
                    chapter_title = line.strip()
                    chapter_title_counts[chapter_title] += 1
                    logger.info(f"检测到章节标题: {chapter_title} (第{chapter_num}章)")
                continue

            if pattern.match(line.strip()):
                if chapter_title:
                    count = chapter_title_counts[chapter_title]
                    suffix = f"_{count}" if count > 1 else ""
                    final_title = chapter_title + suffix
                    chapter_content = '\n'.join(current_chapter).strip()
                    if not chapter_content:
                        chapter_content = final_title
                        logger.warning(f"章节 {chapter_num} 内容为空: {final_title}")
                    chapters.append((chapter_num, final_title, chapter_content))
                    logger.info(f"保存章节 {chapter_num}: {final_title} (内容长度: {len(chapter_content)})")
                    chapter_num += 1
                chapter_title = line.strip()
                chapter_title_counts[chapter_title] += 1
                current_chapter = []
                logger.info(f"检测到新章节标题: {chapter_title} (第{chapter_num}章)")
            else:
                if line.strip():
                    current_chapter.append(line)

        if chapter_title:
            count = chapter_title_counts[chapter_title]
            suffix = f"_{count}" if count > 1 else ""
            final_title = chapter_title + suffix
            chapter_content = '\n'.join(current_chapter).strip()
            if not chapter_content:
                chapter_content = final_title
                logger.warning(f"章节 {chapter_num} 内容为空: {final_title}")
            chapters.append((chapter_num, final_title, chapter_content))
            logger.info(f"保存章节 {chapter_num}: {final_title} (内容长度: {len(chapter_content)})")

        chapter_files = []
        total_chapters = len(chapters)
        chapter_dir = os.path.join(output_dir, 'chapters')
        os.makedirs(chapter_dir, exist_ok=True)
        generated_chapter_nums = set()

        for idx, (num, title, content) in enumerate(chapters):
            if num in generated_chapter_nums:
                logger.warning(f"章节编号 {num} 重复，将跳过")
                continue
            generated_chapter_nums.add(num)
            filename = os.path.join(chapter_dir, f'ch_{num:03d}.txt')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n\n{content}")
            chapter_files.append(filename)
            if FileProcessor.progress_callback:
                FileProcessor.progress_callback(idx + 1, total_chapters)

        if generated_chapter_nums:
            min_num = min(generated_chapter_nums)
            max_num = max(generated_chapter_nums)
            missing_chapters = [num for num in range(min_num, max_num + 1) if num not in generated_chapter_nums]
            if missing_chapters:
                logger.warning(f"检测到缺失章节: {', '.join(map(str, missing_chapters))}")
                logger.info("跳过缺失章节的文件编号")

        logger.info(
            f"成功分割 {len(chapter_files)} 个章节 (从第{min(generated_chapter_nums, default=0)}章到第{max(generated_chapter_nums, default=0)}章)")
        return chapter_files

    @staticmethod
    def get_chapter_files(output_dir):
        chapter_dir = os.path.join(output_dir, 'chapters')
        if not os.path.exists(chapter_dir):
            return []
        return sorted(
            [os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir) if f.endswith('.txt')],
            key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
        )

    @staticmethod
    def load_summary(summary_path):
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    @staticmethod
    def export_summary_excel(output_dir):
        summary_dir = os.path.join(output_dir, 'stage1_summaries')
        if not os.path.exists(summary_dir):
            return None
        summaries = []
        for fname in os.listdir(summary_dir):
            if fname.endswith('.json'):
                summary_path = os.path.join(summary_dir, fname)
                data = FileProcessor.load_summary(summary_path)
                if data:
                    data['chapter_file'] = f"ch_{data['chapter']:03d}.txt"
                    summaries.append(data)
        if not summaries:
            return None
        df = pd.DataFrame(summaries)
        excel_path = os.path.join(output_dir, 'chapter_summaries.xlsx')
        df.to_excel(excel_path, index=False)
        return excel_path