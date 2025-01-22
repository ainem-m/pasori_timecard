import sys
from enum import Enum
from typing import Callable, Optional

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QTimeLine
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ButtonState(Enum):
    NORMAL = 0
    PRESSING = 1
    LONG_PRESSED = 2


class LongPressButton(QPushButton):
    """長押し検出と液体充填アニメーション付きのボタンウィジェット。"""

    def __init__(
        self,
        text: str,
        parent: Optional[QWidget] = None,
        long_press_callback: Optional[Callable[[QPushButton], None]] = None,
    ):
        """LongPressButton を初期化します。"""
        super().__init__(text, parent)
        self.state = ButtonState.NORMAL
        self.long_press_callback = long_press_callback
        self.long_press_duration = 1000  # ミリ秒

        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setDuration(self.long_press_duration)
        self.animation.setEasingCurve(QEasingCurve.OutElastic)
        self.original_size = self.size()

        self.end_animation = QPropertyAnimation(self, b"size")
        self.end_animation.setDuration(300)
        self.end_animation.setEasingCurve(QEasingCurve.OutBounce)

        self.fill_timeline = QTimeLine(self.long_press_duration, self)
        self.fill_timeline.setEasingCurve(QEasingCurve.Linear)
        self.fill_timeline.valueChanged.connect(self.update_liquid_fill)
        self.fill_timeline.finished.connect(self.on_fill_finished)

        self.fill_height = 0
        self.fill_color = QColor(200, 128, 200, 128)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.state == ButtonState.NORMAL:
            self.state = ButtonState.PRESSING
            self.fill_timeline.start()
            self.animation.setStartValue(self.size())
            self.animation.setEndValue(self.size() * 0.95)
            self.animation.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.state == ButtonState.PRESSING:
            self.state = ButtonState.NORMAL
            self.fill_timeline.stop()
            self.animation.stop()
            self.animation.setStartValue(self.size())
            self.animation.setEndValue(self.original_size)
            self.animation.start()
        super().mouseReleaseEvent(event)

    def on_fill_finished(self):
        if self.state == ButtonState.PRESSING:  # releaseされてない場合のみ実行
            self.state = ButtonState.LONG_PRESSED
            if self.long_press_callback:
                self.long_press_callback(self)
            self.end_animation.setStartValue(self.size())
            self.end_animation.setEndValue(self.original_size * 1.05)
            self.end_animation.start()

    def update_liquid_fill(self, value: float):
        self.fill_height = int(self.height() * value)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.state != ButtonState.NORMAL:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            liquid_rect = QRectF(
                0, self.height() - self.fill_height, self.width(), self.fill_height
            )
            painter.setBrush(QBrush(self.fill_color))
            painter.drawRect(liquid_rect)
            painter.end()

    def deleteLater(self):
        self.fill_timeline.stop()
        self.fill_timeline.deleteLater()
        self.animation.deleteLater()
        self.end_animation.deleteLater()
        super().deleteLater()


def show_accept_dialog(parent: QWidget) -> bool:
    """確認ダイアログを表示する。"""
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Information)
    dialog.setWindowTitle("Confirm Action")
    dialog.setText("Do you want to accept?")
    dialog.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
    )
    result = dialog.exec()
    return result == QMessageBox.StandardButton.Ok


def on_long_press_callback(button: QPushButton):
    """長押し後の処理。"""
    print("Button long pressed!")
    button.setText("Long Pressed!")
    if show_accept_dialog(button.parentWidget()):
        print("Accept clicked! Closing application.")
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    long_press_button = LongPressButton(
        "Press and Hold", window, on_long_press_callback
    )
    layout.addWidget(long_press_button)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())
