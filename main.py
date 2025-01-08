from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from loguru import logger
import config
from pathlib import Path
from auto_close_window import AutoCloseMessageBox

logger.add(config.LOG_FILE_PATH, level="TRACE", rotation="10 MB")


@logger.catch
def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    # TODO: データベースファイルが作成されていない場合に、作成したい
    # initialize.pyに初期化処理を切り分ける？
    list_file = Path(config.EMPLOYEE_LIST)
    if not list_file.exists():
        raise FileNotFoundError("まず最初にlist_editor.pyを起動してください")
    db_file = Path(config.DATABASE_PATH)
    if not db_file.exists():
        raise FileNotFoundError(
            "データベースが見つかりません。db_alchemy.pyを起動してください。"
        )
    main()
