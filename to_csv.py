import csv
from datetime import datetime, timedelta
from db_alchemy import Employee, AttendanceRecord
import time_util
from collections import defaultdict
import config
from typing import Optional, Union
from pathlib import Path
import sys


TIME_FORMAT = "%Y/%m/%d(%a)"
BLANK = "-"  # 使用していないところの時刻表示
LOST = "##:##"  # 押し忘れの時刻表示
HEADER = [
    "日付",
    "出勤1",
    "退勤1",
    "出勤2",
    "退勤2",
    "要確認",
]
BLANK_LINE = [BLANK] * len(HEADER)


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
    has_lost = False
    punch_pairs = []

    punches.reverse()  # リストを逆順にして処理しやすくする

    while punches:
        punch_type, punch_time = punches.pop()
        if punch_type.name == "IN":  # "IN"の場合
            if punches and punches[-1][0].name == "OUT":  # 次が"OUT"ならペアにする
                _, next_time = punches.pop()
                punch_pairs.append((punch_time, next_time))
            else:  # 次が"OUT"でない、または打刻がない場合
                punch_pairs.append((punch_time, None))
                has_lost = True
        elif punch_type.name == "OUT":  # "OUT"のみの場合
            punch_pairs.append((None, punch_time))
            has_lost = True

    return punch_pairs, has_lost


def export_employee_attendance_to_csv(year: int, month: int):
    output_dir = Path(config.CSV_PATH) / f"{year}-{month:02d}"

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
    end_date = now + one_day
    """従業員ごとの勤怠記録をCSVに出力する"""
    # 全従業員を取得
    employees = Employee.get_all()

    for employee in employees:
        # 従業員の全勤怠記録を取得、ここで昇順になっていることが保証される
        records = AttendanceRecord.get_employee_records(
            employee_id=employee.employee_id, start_date=start_date, end_date=end_date
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

                punch_pairs, has_lost = make_pairs(punches)

                if punch_pairs is None:
                    continue

                # 最大2ペアまで対応（出勤1～2、退勤1～2）
                for i in range(2):
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

                # 押し忘れがあるかどうか
                row.append("有り" if has_lost else "-")

                # 行をCSVに書き込む
                writer.writerow(row)
            writer.writerow([employee.name])
        print(
            f"{employee.name} の勤怠データを {output_dir}/{employee.name}.csv に書き出しました。"
        )


if __name__ == "__main__":
    input_str: str
    if len(sys.argv) != 2:
        input_str = input("年と月を入力 例: 2024/08, 2024/8, 24/08, 24/8 ->")
    else:
        input_str = sys.argv[1]
    export_employee_attendance_to_csv(*time_util.parse_date_string(input_str))
