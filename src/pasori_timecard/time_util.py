from datetime import datetime, timedelta
import pytz
import re

TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
TZ = pytz.timezone("Asia/Tokyo")
ONE_DAY = timedelta(days=1)


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


def get_billing_period(
    year: int, month: int, start_day: int
) -> tuple[datetime, datetime]:
    """
    指定した年・月の「締め日翌日から次の締め日まで」の期間を求める。

    Parameters:
        year (int): 対象の年
        month (int): 対象の月
        start_day (int): 締め日（開始日）

    Returns:
        tuple[datetime, datetime]: (開始日, 終了日)
    """
    # 1月の場合、前年の12月から計算
    if month == 1:
        start_date = datetime(year=year - 1, month=12, day=start_day)
        end_date = datetime(year=year, month=1, day=start_day) - ONE_DAY
    else:
        start_date = datetime(year=year, month=month - 1, day=start_day)
        end_date = datetime(year=year, month=month, day=start_day) - ONE_DAY

    return start_date, end_date


def get_date_list(
    start_date: datetime, end_date: datetime, time_format: str = TIME_FORMAT
) -> list[str]:
    """
    指定した開始日と終了日の間の日付リストを作成する。

    Parameters:
        start_date (datetime): 期間の開始日
        end_date (datetime): 期間の終了日
        time_format (str): 期間リストのフォーマット（デフォルト: "YYYY-MM-DD"）

    Returns:
        list[str]: 期間のフォーマットされた日付リスト
    """
    date_list = []
    now = start_date

    while now <= end_date:
        date_list.append(now.strftime(time_format))
        now += ONE_DAY

    return date_list


def days_ago(days):
    return current_time() - ONE_DAY * days


if __name__ == "__main__":
    # テスト
    year = 2025
    month = 2
    start, end = get_billing_period(year, month, 16)
    print(get_date_list(start, end))
    print(days_ago(7))
