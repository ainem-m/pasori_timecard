from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QLabel
from config import TIME_OUT
import time


class AutoCloseMessageBox(QMessageBox):
    """
    自動で閉じるQMessageBoxのクラス

    :param timeout: ダイアログが閉じるまでの時間（ミリ秒）
    """

    def __init__(self, title="", text="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.timeout = TIME_OUT
        self.title = title
        self.setText(f"{self.text} \n {self.timeout}秒で自動で閉じます")
        self.setWindowTitle(self.title)

        # タイマーを設定し、指定した時間後にダイアログを閉じる
        self.timer = QTimer(self)
        self.setIcon(QMessageBox.Warning)
        self.addButton(QMessageBox.Ok)
        self.timer.timeout.connect(self.countdown)  # OKボタンを押すのと同様の動作
        self.timer.start(1000)

    def countdown(self):
        self.timeout -= 1
        self.setText(f"{self.text} \n {self.timeout}秒で自動で閉じます")

        if self.timeout <= 0:
            self.accept()


if __name__ == "__main__":
    start = time.time()
    app = QApplication([])
    print(time.time() - start)
    msg = AutoCloseMessageBox(title="エラー", text="テストです")
    print(time.time() - start)
    msg.show()
    print(time.time() - start)

    app.exec()
