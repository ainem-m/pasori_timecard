# config.py


DEBUG: bool = True

# 締め日
START_DAY = 16

# SQLiteデータベースの設定
DATABASE_PATH = "nfc_records.db"  # データベースファイルのパス
EMPLOYEE_LIST = "employee_list.txt"

# GUIの設定
WINDOW_SIZE: tuple[int, int] = (480, 400)  # ウィンドウのサイズ


class StyleSheets:
    waiting = "font-size: 32px; font-weight: bold;"
    time_display: str = "font-size: 72px; font-weight: bold; color: #333333;"
    bg_punch_in: str = (
        "font-size: 24px; font-weight:bold; background-color: #FFCC99; color: black;"
    )
    bg_punch_out: str = (
        "font-size: 24px; font-weight:bold; background-color: #2C3E50; color: white;"
    )


# 自動で閉じるウィンドウのタイマー設定
TIME_OUT: int = 10

# ログファイルの設定(未実装)
LOG_FILE_PATH: str = "application.log"  # ログファイルのパス


class MessageTexts:

    waiting = "ICカードをスキャンしてください"

    @staticmethod
    def greeting(name: str, punch_time: str, record_type):

        greet_punch_in = "おはようございます。"
        greet_punch_out = "お疲れ様でした。"
        if record_type.value == "出勤":
            greet = greet_punch_in
        elif record_type.value == "退勤":
            greet = greet_punch_out
        ### 打刻時のメッセージ ##########################
        return f"{name}さん、{greet}\n {punch_time}に{record_type.value}です"

    @staticmethod
    def punching(seconds: int) -> str:
        return f"{seconds}秒後に自動で記録します"
