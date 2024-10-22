import csv
from datetime import datetime, timedelta
from db_alchemy import Employee, AttendanceRecord
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time_util
from collections import defaultdict
from config import DATABASE_PATH
from typing import Optional
from pathlib import Path
import sys

# SQLiteエンジンを作成し、データベースに接続
engine = create_engine(f"sqlite:///{DATABASE_PATH}")
Session = sessionmaker(bind=engine)

BLANK = "--:--"  # 使用していないところの時刻表示
LOST = "##:##"  # 押し忘れの時刻表示
DIR_NAME = "csv"


def export_employee_attendance_to_csv(year: int, month: int):
    output_dir = Path(f"{DIR_NAME}/{year}-{month:02d}")

    # 出力フォルダを作成 存在する場合は上書き
    output_dir.mkdir(exist_ok=True, parents=True)
    # 調べる期間のdatetimeのリスト
    # その月の16日から次の月の15日まで
    one_day = timedelta(days=1)
    day = 16
    now = datetime(year=year, month=month - 1, day=day)
    period: list[str] = [now.date().strftime("%m/%d(%a)")]
    while day != 15:
        period.append(now.date().strftime("%m/%d(%a)"))
        now += one_day
        day = now.day
    """従業員ごとの勤怠記録をCSVに出力する"""
    with Session() as session:
        # 全従業員を取得
        employees = session.query(Employee).all()

        for employee in employees:
            # 従業員の全勤怠記録を取得、ここで昇順になっていることが保証される
            records = (
                session.query(AttendanceRecord)
                .filter_by(employee_id=employee.employee_id)
                .order_by(AttendanceRecord.record_time)
                .all()
            )

            if not records:
                print(f"{employee.name} の勤怠記録が見つかりませんでした。")
                continue

            # 日付ごとに勤怠を整理するためのデータ構造を用意
            daily_attendance = defaultdict(list)

            # 勤怠記録を日付ごとに整理
            for record in records:
                date_ = record.record_time.date()
                date = date_.strftime("%m/%d(%a)")
                record_type = record.record_type
                record_time = record.record_time
                daily_attendance[date].append((record_type, record_time))

            # CSVファイルを従業員名で開く
            with open(
                output_dir / f"{employee.name}.csv",
                mode="w",
                newline="",
                encoding="utf-8",
            ) as csv_file:
                writer = csv.writer(csv_file)

                # ヘッダー行を書き込む
                header = [
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
                    "押し忘れ",
                ]
                writer.writerow(header)

                # 日付ごとに出勤・退勤をペアにして書き込む
                for date in period:
                    punches = daily_attendance[date]
                    if len(punches) == 0:
                        writer.writerow(
                            [
                                "--/--(---)",
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                BLANK,
                                "-",
                            ]
                        )
                        continue

                    def calc_duration(start: datetime, stop: datetime) -> int:
                        assert start < stop
                        hours = stop.hour - start.hour
                        minutes = stop.minute - start.minute
                        total_minutes = hours * 60 + minutes
                        return total_minutes

                    row = [date]

                    # 勤務時間の合計を計算するための変数
                    total_work_duration = 0

                    punch_pairs: list[tuple[Optional[datetime], Optional[datetime]]] = (
                        []
                    )
                    punch_in_time = None
                    has_lost = False

                    for punch_type, punch_time in punches:
                        if punch_type.name == "IN":
                            # 出勤を記録
                            if punch_in_time is None:
                                punch_in_time = punch_time
                            else:
                                # 退勤が押されてなかった場合
                                punch_pairs.append((punch_in_time, None))
                                has_lost = True
                        elif punch_type.name == "OUT":
                            if punch_in_time is not None:
                                punch_pairs.append((punch_in_time, punch_time))
                                total_work_duration += calc_duration(
                                    start=punch_in_time, stop=punch_time
                                )
                                punch_in_time = None
                            else:
                                # 出勤が押されていなかった場合
                                punch_pairs.append((None, punch_time))
                                has_lost = True

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

            print(
                f"{employee.name} の勤怠データを {output_dir}/{employee.name}.csv に書き出しました。"
            )


def parse_date_string(date_str: str) -> tuple[int, int]:
    # Detect if it's separated by '/' or '-'
    separator = "/" if "/" in date_str else "-"

    # Split by the separator
    year_str, month_str = date_str.split(separator)

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
        input_str = input("年と月を入力 例: 2024/10 ->")
    else:
        input_str = sys.argv[1]
    parse_date_string(input_str)
    export_employee_attendance_to_csv(*parse_date_string(input_str))
