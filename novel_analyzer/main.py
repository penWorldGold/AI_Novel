# main.py
import logging
from ui.app import NovelAnalyzerApp

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("novel_analyzer.log"),
            logging.StreamHandler()
        ]
    )
    app = NovelAnalyzerApp()
    app.mainloop()