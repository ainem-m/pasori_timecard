import csv
from datetime import datetime, timedelta
from db_alchemy import Employee, AttendanceRecord
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time_util
from collections import defaultdict
import config
from typing import Optional, Union
from pathlib import Path
import sys
import re

# SQLiteエンジンを作成し、データベースに接続
engine = create_engine(f"sqlite:///{config.DATABASE_PATH}")
Session = sessionmaker(bind=engine)

TIME_FORMAT = "%Y/%m/%d(%a)"
BLANK = "-"  # 使用していないところの時刻表示
LOST = "##:##"  # 押し忘れの時刻表示
DIR_NAME = "csv"
HEADER = [
    "日付",
    "出勤1",
    "退勤1",
    "出勤2",
    "退勤2",
    "出勤3",
    "退勤3",
    "出勤4",
    "退勤4",
    "勤務時間",
    "要確認",
]
BLANK_LINE = [BLANK] * len(HEADER)


def calc_duration(start: datetime, stop: datetime) -> int:
    assert start < stop
    hours = stop.hour - start.hour
    minutes = stop.minute - start.minute
    total_minutes = hours * 60 + minutes
    return total_minutes


def make_pairs(punches):
    """
    打刻データをペアリングする関数。

    Args:
        punches (list[tuple]): 打刻データ [(type, time), ...]。
                               type は "IN" または "OUT"。
    Returns:
        tuple: (punch_pairs, has_lost)
               punch_pairs: [(IN_time, OUT_time), ...]
               has_lost: True ifペアリングに失敗した打刻がある場合。
    """
    total_work_duration = 0
    has_lost = False
    punch_pairs = []

    punches.reverse()  # リストを逆順にして処理しやすくする

    while punches:
        punch_type, punch_time = punches.pop()
        if punch_type.name == "IN":  # "IN"の場合
            if punches and punches[-1][0].name == "OUT":  # 次が"OUT"ならペアにする
                _, next_time = punches.pop()
                punch_pairs.append((punch_time, next_time))
                total_work_duration += calc_duration(punch_time, next_time)
            else:  # 次が"OUT"でない、または打刻がない場合
                punch_pairs.append((punch_time, None))
                has_lost = True
        elif punch_type.name == "OUT":  # "OUT"のみの場合
            punch_pairs.append((None, punch_time))
            has_lost = True

    return punch_pairs, has_lost, total_work_duration


def export_employee_attendance_to_csv(year: int, month: int):
    output_dir = Path(f"{DIR_NAME}/{year}-{month:02d}")

    # 出力フォルダを作成 存在する場合は上書き
    output_dir.mkdir(exist_ok=True, parents=True)
    # 調べる期間のdatetimeのリスト
    # その月の締め日の次の日から次の月の締め日まで
    one_day = timedelta(days=1)
    day = config.START_DAY
    if month == 1:
        # 1月が指定された場合、前の年の12月から計算する
        year -= 1
        month = 13
    now = datetime(year=year, month=month - 1, day=day)
    start_date = now
    period: list[str] = []
    while day != config.START_DAY - 1:
        period.append(now.date().strftime(TIME_FORMAT))
        now += one_day
        day = now.day
    period.append(now.date().strftime(TIME_FORMAT))
    end_date = now
    """従業員ごとの勤怠記録をCSVに出力する"""
    with Session() as session:
        # 全従業員を取得
        employees = session.query(Employee).all()

        for employee in employees:
            # 従業員の全勤怠記録を取得、ここで昇順になっていることが保証される
            records = (
                session.query(AttendanceRecord)
                .filter_by(employee_id=employee.employee_id)
                .filter(
                    start_date <= AttendanceRecord.record_time,
                    AttendanceRecord.record_time <= end_date,
                )
                .order_by(AttendanceRecord.record_time)
                .all()
            )
            if not records:
                print(f"{employee.name} の勤怠記録が見つかりませんでした。")
                # continue 勤怠記録なしでもcsv出力する

            # 日付ごとに勤怠を整理するためのデータ構造を用意
            daily_attendance = defaultdict(list)

            # 勤怠記録を日付ごとに整理
            for record in records:
                date_ = record.record_time.date()
                date = date_.strftime(TIME_FORMAT)
                record_type = record.record_type
                record_time = record.record_time
                daily_attendance[date].append((record_type, record_time))

            # CSVファイルを従業員名で開く
            with open(
                output_dir / f"{employee.name}.csv",
                mode="w",
                newline="",
                # encoding="utf-8",
                encoding="utf-8-sig",  # UTF-8 (BOM付き)を指定
            ) as csv_file:
                writer = csv.writer(csv_file)

                # ヘッダー行を書き込む

                writer.writerow(HEADER)

                # 日付ごとに出勤・退勤をペアにして書き込む
                for date in period:
                    punches = daily_attendance[date]
                    if len(punches) == 0:
                        writer.writerow(BLANK_LINE)
                        continue

                    row = [date]

                    punch_pairs, has_lost, total_work_duration = make_pairs(punches)

                    if punch_pairs is None:
                        continue

                    # 最大4ペアまで対応（出勤1～4、退勤1～4）
                    for i in range(4):
                        if i >= len(punch_pairs):
                            # 出勤退勤のペアが4未満の場合、空白を追加してフォーマットを揃える
                            row.append(BLANK)
                            row.append(BLANK)
                            continue
                        punch_in, punch_out = punch_pairs[i]
                        if punch_in is not None:
                            row.append(time_util.datetime_to_string(punch_in, "%H:%M"))
                        else:
                            row.append(LOST)
                        if punch_out is not None:
                            row.append(time_util.datetime_to_string(punch_out, "%H:%M"))
                        else:
                            row.append(LOST)

                    # 勤務時間を計算して追加
                    total_hours, total_minutes = divmod(total_work_duration, 60)
                    row.append(f"{total_hours:02d}:{total_minutes:02d}")

                    # 押し忘れがあるかどうか
                    row.append("有り" if has_lost else "-")

                    # 行をCSVに書き込む
                    writer.writerow(row)
                writer.writerow([employee.name])
            print(
                f"{employee.name} の勤怠データを {output_dir}/{employee.name}.csv に書き出しました。"
            )


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


if __name__ == "__main__":
    input_str: str
    if len(sys.argv) != 2:
        input_str = input("年と月を入力 例: 2024/08, 2024/8, 24/08, 24/8 ->")
    else:
        input_str = sys.argv[1]
    export_employee_attendance_to_csv(*parse_date_string(input_str))
