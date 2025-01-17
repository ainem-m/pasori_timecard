from datetime import datetime
import pytz
import re

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


def parse_date_string(date_str):
    # Validate input format using regex (allows YYYY/MM, YY/MM, YYYY/M, YY/M, etc.)
    if not re.match(r"^\d{2,4}[-/]\d{1,2}$", date_str):
        raise ValueError("以下の形式で入力してください: YYYY/MM, YY/MM, YYYY/M, YY/M")

    # Detect if it's separated by '/' or '-'
    separator = "/" if "/" in date_str else "-"

    # Split by the separator
    year_str, month_str = date_str.split(separator)

    # Validate year and month ranges
    if not (1 <= int(month_str) <= 12):
        raise ValueError(
            "1月から12月の範囲で入力してください フォーマット: YYYY/MM, YY/MM, YYYY/M, YY/M"
        )

    # Process year
    if len(year_str) == 2:
        year = 2000 + int(year_str) if int(year_str) < 50 else 1900 + int(year_str)
    else:
        year = int(year_str)

    # Process month
    month = int(month_str)

    return (year, month)
