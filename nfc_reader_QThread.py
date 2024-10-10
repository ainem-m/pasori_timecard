from PySide6.QtCore import QThread, Signal
import nfc
from typing import Callable, Optional


class NfcReaderMock(QThread):
    """NFCリーダーがつながっていない場合にテストするためのダミークラス"""

    nfc_connected = Signal(str)
    test_id = "test"

    def __init__(self):
        super().__init__()

    def run(self):
        pass


class NfcReader(QThread):
    """NFCリーダーをQThreadで動作させるクラス
    読み取りが完了したらon_connectを実行し、結果をメインスレッドに通知
    """

    nfc_connected = Signal(str)  # 読み取ったICカードIDをシグナルで送る

    def __init__(
        self, clf: nfc.ContactlessFrontend, on_connect: Optional[Callable] = None
    ):
        super().__init__()
        self.on_connect = on_connect or self.default_on_connect
        self.clf = clf

    def default_on_connect(self, tag):
        ic_card_id = str(tag.identifier.hex())  # カードのIDを取得
        print(f"ICカードIDを読み取りました: {ic_card_id}")
        self.nfc_connected.emit(ic_card_id)  # メインスレッドにシグナルを送る
        return True

    def on_startup(self, targets):
        """iphoneのエキスプレスカードに対応するため、この関数でsystem_idを指定しなければならない。
        今回は交通系Felicaの`0003`
        詳しくはhttp://hara-jp.com/_default/ja/Topics/RaspPiCardReader.html
        他のカードにも対応する場合に変更が必要かもしれない
        """
        for target in targets:
            target.sensf_req = bytearray.fromhex("0000030000")
        return targets

    def run(self):
        self.clf.connect(
            rdwr={
                "targets": ["212F", "424F"],
                "on-startup": self.on_startup,
                "on-connect": self.on_connect,
            }
        )


if __name__ == "__main__":
    nfc_reader = NfcReader(nfc.ContactlessFrontend("usb"))
    nfc_reader.run()
