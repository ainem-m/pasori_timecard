from PySide6.QtCore import QThread, Signal
import nfc
from typing import Callable, Optional
import time


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
    https://github.com/haraisao/nfc_reader を多分に参考にしています
    """

    nfc_connected = Signal(str)  # 読み取ったICカードIDをシグナルで送る

    def __init__(
        self, clf: nfc.ContactlessFrontend, on_connect: Optional[Callable] = None
    ):
        super().__init__()
        self.on_connect = on_connect or self.default_on_connect
        self.clf = clf
        self.toggle = True
        self.suica = self.set_felica("0003")  # iphone エキスプレスカード
        self.blank = self.set_felica("FFFF")  # felica ブランクカード
        self.targets = [self.blank]  # iphone以外のカードをここにまとめる

    def set_felica(self, sys_id):
        target = nfc.clf.RemoteTarget("212F")
        target.sensf_req = bytearray.fromhex(f"00{sys_id}0000")
        return target

    def sense(self):
        """
        NFCカード検出メソッド。

        `toggle`の状態に応じて`suica`専用のターゲットリストと他のターゲットリストを交互に切り替えて検出

        iPhoneのエクスプレスカードが選択画面を表示しないよう、`suica`のみターゲットにする時間を設定している。
        `suica`のみターゲットにする時間を長くするために、`iterations`を調整

        Returns:
            target (nfc.clf.RemoteTarget || None): 検出されたターゲット。見つからなければ`None`。
        """
        if self.toggle:
            self.target = self.clf.sense(self.suica, iterations=15, interval=0.1)
        else:
            self.target = self.clf.sense(*self.targets, iterations=1, interval=0.1)
        self.toggle = not self.toggle
        return self.target

    def default_on_connect(self, tag):
        ic_card_id = str(tag.identifier.hex())  # カードのIDを取得
        print(f"ICカードIDを読み取りました: {ic_card_id}")
        self.nfc_connected.emit(ic_card_id)  # メインスレッドにシグナルを送る
        return True

    def on_discover(self, target):
        if target is None:
            return False
        elif target.sel_res and target.sel_res[0] & 0x40:
            return False
        elif target.sensf_res and target.sensf_res[1:3] == b"\x01\xFE":
            return False
        else:
            return True

    def run(self):
        while self.sense() is None:
            time.sleep(0.1)
        if self.on_discover(self.target):
            tag = nfc.tag.activate(self.clf, self.target)
            self.on_connect(tag)
            return


if __name__ == "__main__":

    nfc_reader = NfcReader(nfc.ContactlessFrontend("usb"))
    nfc_reader.run()
