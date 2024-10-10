from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QPushButton,
)
from PySide6.QtCore import QTimer
import db_alchemy
from config import TIME_OUT, WINDOW_SIZE, MessageTexts, StyleSheets
from datetime import datetime
import time_util
from typing import Optional


class PunchDialog(QDialog):
    """
    args
    ic_card_id:str
    punch_time:QDateTime

    MainWindowでICカードの読み取りを検出したときに表示されるウィンドウ。
    ic_card_id（ICカードのID）とpunch_time（打刻時刻）を引数として受け取る。
    ic_card_idと紐づけられた従業員の最終打刻記録を取得し、最終打刻の状態に応じて「出勤」または「退勤」を決定する。
    ウィンドウには従業員名、打刻時刻、および現在の「出勤」または「退勤」の状態が表示され、必要に応じて出勤/退勤を切り替えるためのトグルボタンも表示する。
    ダイアログは一定時間表示され、トグルボタンが押された場合はタイマーがリセットされる。ダイアログが消えるときに、出勤/退勤の情報がデータベースに記録される。
    """

    def __init__(self, ic_card_id: str, punch_time: datetime, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.timeout = TIME_OUT
        self.employee = db_alchemy.IC_Card.find_employee_by_ic_card_number(ic_card_id)
        assert self.employee is not None
        self.punch_time = punch_time
        self.last_record = db_alchemy.AttendanceRecord.get_last_record(self.employee)
        self.current_status: db_alchemy.RecordType = self.determine_status()

        self._gui_init()
        self._init_timer()

    def _gui_init(self):
        self.setWindowTitle("打刻確認")
        self.resize(*WINDOW_SIZE)

        # ラベルとボタンの作成
        self.status_label = QLabel("打刻確認")
        self.countdown_label = QLabel(MessageTexts.punching(self.timeout))
        self.toggle_button = QPushButton("状態を変更")
        self.toggle_button.setStyleSheet("font-size: 24px;")
        # self.toggle_button.setFixedSize(200, 100)
        self.toggle_button.clicked.connect(self.toggle_status)

        self.ok_button = QPushButton("キャンセル")
        self.ok_button.clicked.connect(self.reject)  # OKを押したらダイアログを閉じる
        self.status_label.setText(
            MessageTexts.greeting(
                self.employee.name,
                time_util.datetime_to_string(self.punch_time),
                self.current_status,
            )
        )

        # レイアウトの設定
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.countdown_label)
        layout.addWidget(self.toggle_button)
        layout.setSpacing(50)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        if self.current_status == db_alchemy.RecordType.IN:
            self.setStyleSheet(StyleSheets.bg_punch_in)
        elif self.current_status == db_alchemy.RecordType.OUT:
            self.setStyleSheet(StyleSheets.bg_punch_out)

    def determine_status(self) -> db_alchemy.RecordType:
        """本日初めての打刻かどうかを判断する"""
        if self.last_record is None:
            # これまで打刻記録がない場合は初めての打刻
            return db_alchemy.RecordType.IN

        # 最後の打刻がの日付
        last_punch_date: datetime = self.last_record.record_time

        print("打刻の日付", last_punch_date.date(), self.punch_time.date())
        if last_punch_date.date() < self.punch_time.date():
            # 最後の打刻より日付が新しければ、本日始めての打刻
            return db_alchemy.RecordType.IN
        elif last_punch_date.date() == self.punch_time.date():
            print("最後の打刻", self.last_record.record_type)
            # 本日二回目以降の打刻であれば前の打刻と反対の打刻
            if self.last_record.record_type == db_alchemy.RecordType.IN:
                print(self.last_record.record_type, "なので、退勤")
                return db_alchemy.RecordType.OUT
            else:
                print(self.last_record.record_type, "なので、出勤")
                print(type(self.last_record.record_type))
                return db_alchemy.RecordType.IN
        else:
            raise ValueError

    def _init_timer(self):
        # タイマーを設定し、指定した時間後にダイアログを閉じる
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.countdown)
        self.timer.start(1000)

    def countdown(self):
        self.timeout -= 1
        self.countdown_label.setText(MessageTexts.punching(self.timeout))
        if self.timeout <= 0:
            self.accept()

    def accept(self):
        # 打刻処理をしてウィンドウを閉じる
        db_alchemy.AttendanceRecord.punch(
            self.employee.employee_id, self.current_status, self.punch_time
        )
        super().accept()

    def toggle_status(self):
        """トグルボタンがクリックされたときに状態を変更する
        TODO 背景も変えたい"""

        self.current_status = (
            db_alchemy.RecordType.IN
            if self.current_status == db_alchemy.RecordType.OUT
            else db_alchemy.RecordType.OUT
        )
        if self.current_status == db_alchemy.RecordType.IN:
            self.setStyleSheet(StyleSheets.bg_punch_in)
        elif self.current_status == db_alchemy.RecordType.OUT:
            self.setStyleSheet(StyleSheets.bg_punch_out)

        self.timeout = TIME_OUT
        self.countdown_label.setText(MessageTexts.punching(self.timeout))
        self.status_label.setText(
            MessageTexts.greeting(
                self.employee.name,
                time_util.datetime_to_string(self.punch_time),
                self.current_status,
            )
        )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    test: Optional[db_alchemy.Employee] = db_alchemy.Employee.get_by_name("テスト")
    assert test is not None
    test_cards = test.ic_card_list()
    assert test_cards is not None
    test_card = test_cards[0]
    app = QApplication([])
    window = PunchDialog(
        test_card.ic_card_number,
        time_util.current_time(),
    )
    window.show()

    app.exec()
