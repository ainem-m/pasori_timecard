from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from loguru import logger
from config import LOG_FILE_PATH
import sys

logger.add(LOG_FILE_PATH, level="TRACE", rotation="10 MB")


@logger.catch
def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
