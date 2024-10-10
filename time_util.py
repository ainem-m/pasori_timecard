from datetime import datetime
import pytz


TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
TZ = pytz.timezone("Asia/Tokyo")


def current_time():
    return datetime.now(TZ)


def datetime_to_string(dt: datetime, format: str = TIME_FORMAT) -> str:
    """
    datetimeオブジェクトをフォーマットされた文字列に変換します。

    Args:
        dt (datetime): 変換するdatetimeオブジェクト。
        format (str): 変換に使用するフォーマット文字列。

    Returns:
        str: フォーマットされたdatetime文字列。
    """
    return dt.strftime(format)


def string_to_datetime(date_str: str, format: str = TIME_FORMAT) -> datetime:
    """
    フォーマットされた文字列をdatetimeオブジェクトに変換します。

    Args:
        date_str (str): 変換する文字列。
        format (str): 変換に使用するフォーマット文字列。

    Returns:
        datetime: 結果のdatetimeオブジェクト。
    """
    return datetime.strptime(date_str, format)
