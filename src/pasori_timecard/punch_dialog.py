from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import QTimer
import db_alchemy
from config import TIME_OUT, WINDOW_SIZE, MessageTexts, StyleSheets, HISTORY_DAYS
import time_util
from typing import Optional
import to_csv


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

    def __init__(self, ic_card_id: str, punch_time, *args, **kwargs):
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
        self.toggle_button.clicked.connect(self.toggle_status)

        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(
            self.reject
        )  # キャンセルを押したらダイアログを閉じる
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet(
            """
                QPushButton {
                    font-weight: bold;
                    border: 3px solid white;
                    padding: 10px;
                }
            """
        )
        self.ok_button.clicked.connect(self.accept)  # OKを押したらダイアログを閉じる
        self.status_label.setText(
            MessageTexts.greeting(
                self.employee.name,
                time_util.datetime_to_string(self.punch_time),
                self.current_status,
            )
        )
        start_date, end_date = (
            time_util.days_ago(HISTORY_DAYS),
            time_util.current_time(),
        )
        period = time_util.get_date_list(
            start_date, end_date + time_util.ONE_DAY, to_csv.TIME_FORMAT
        )
        records = db_alchemy.AttendanceRecord.get_employee_records(
            employee_id=self.employee.employee_id, start_date=start_date
        )
        data = to_csv.make_data(records, period)
        # 右側の新しいテキスト
        self.info_label = QTableWidget(HISTORY_DAYS + 1, len(to_csv.BLANK_LINE))
        self.info_label.setHorizontalHeaderLabels(to_csv.HEADER)
        self.info_label.setStyleSheet(
            """
            QTableWidget { font-size: 10pt; } 
            QHeaderView::section { font-size: 10pt; }
        """
        )
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                self.info_label.setItem(i, j, QTableWidgetItem(value))
        self.info_label.verticalHeader().setVisible(False)
        self.info_label.resizeColumnsToContents()
        # メインレイアウト（横方向）
        main_layout = QHBoxLayout()

        # 右側のレイアウト（タイムカード）
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.info_label)

        # 左側のレイアウト
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.status_label)
        left_layout.addWidget(self.countdown_label)
        left_layout.addWidget(self.toggle_button)
        left_layout.setSpacing(50)

        # ボタン用のレイアウト（横方向）
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        # 左側のレイアウトにボタンを追加
        left_layout.addLayout(button_layout)

        # ✅ 左右のレイアウトをメインレイアウトに追加（順番を逆に）
        main_layout.addLayout(left_layout)  # 先に元のUI（左側）
        main_layout.addLayout(text_layout)  # 次に文章（右側）

        self.setLayout(main_layout)
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
        last_punch_date = self.last_record.record_time

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
