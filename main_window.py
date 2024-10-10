import nfc
from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

from config import StyleSheets, WINDOW_SIZE, MessageTexts, DEBUG
from auto_close_window import AutoCloseMessageBox
from punch_dialog import PunchDialog
from nfc_reader_QThread import NfcReader, NfcReaderMock
import db_alchemy
import time_util


class TimeDisplay(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(StyleSheets.time_display)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 1秒ごとに時刻を更新
        self.update_time()  # 最初に時刻を表示

    def update_time(self):
        try:
            current_time = time_util.current_time()
            self.setText(time_util.datetime_to_string(current_time, "%m/%d %H:%M:%S"))
        except KeyboardInterrupt:
            print("KeyboardInterrupt 終了します")
            exit()


class MainWindow(QMainWindow):
    """main.pyから呼び出されるメインウィンドウ
    文章と時刻が表示されている
    nfc_readerをスレッドで起動し、ICカードを読み込んだらpunch_dialogを呼び出す
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("NFC Reader Example")
        self.resize(*WINDOW_SIZE)

        # ラベルを表示するためのUI要素
        self.label = QLabel(MessageTexts.waiting)
        self.setStyleSheet(StyleSheets.waiting)

        # レイアウトを設定
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        # 時刻表示ラベルの設定
        self.time_display = TimeDisplay()
        layout.addWidget(self.time_display)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # NfcReaderを起動
        try:
            clf = nfc.ContactlessFrontend("usb")
            self.nfc_reader = NfcReader(clf)
        except OSError as e:
            if DEBUG:
                print("デバッグモードで起動します、読み込みボタンを表示します")
                self.nfc_reader = NfcReaderMock()
                self.debug_button = QPushButton("読み込み(未登録カード)")
                self.debug_button.clicked.connect(self.mock_card_read_error)
                layout.addWidget(self.debug_button)
                self.debug_button = QPushButton("読み込み(登録済カード)")
                self.debug_button.clicked.connect(self.mock_card_read)
                layout.addWidget(self.debug_button)
            else:
                msg = AutoCloseMessageBox(
                    title="エラー", text=f"{e}\nカードリーダーを接続してください"
                )
                msg.exec()
                exit()

        self.nfc_reader.nfc_connected.connect(
            self.update_label
        )  # シグナルをスロットに接続

        # スレッドを開始
        self.nfc_reader.start()

    @Slot(str)  # スロットで受け取るデータ型を指定
    def update_label(self, ic_card_id):
        """NFCリーダーからシグナルを受け取ったときに呼び出されるスロット"""
        punch_time = time_util.current_time()
        if db_alchemy.IC_Card.find_employee_by_ic_card_number(ic_card_id):
            dialog = PunchDialog(ic_card_id, punch_time)
            dialog.exec()
        else:
            msg = AutoCloseMessageBox(title="エラー", text="登録されていないカードです")
            msg.exec()
        # nfc_readerを再起動する
        self.nfc_reader.wait()
        self.nfc_reader.start()

    def reset_label(self):
        """ラベルを初期状態にリセット"""
        self.label.setText(MessageTexts.WAITING)

    def mock_card_read_error(self):
        """デバッグ用: ボタンを押すと仮想カードIDを読み込む"""
        # 仮のICカードIDと現在の時刻を使ってスロットを呼び出し
        mock_ic_card_id = "DEBUG_CARD_001"  # 未登録
        self.update_label(mock_ic_card_id)

    def mock_card_read(self):
        """デバッグ用: ボタンを押すと仮想カードIDを読み込む"""
        # 仮のICカードIDと現在の時刻を使ってスロットを呼び出し
        # データベースから適当に一つカードを取得
        mock_ic_card_id = db_alchemy.IC_Card.get_all()[0].ic_card_number
        assert mock_ic_card_id is not None
        self.update_label(mock_ic_card_id)
