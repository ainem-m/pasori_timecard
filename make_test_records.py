from datetime import datetime, timedelta
import random
from db_alchemy import Employee, AttendanceRecord, RecordType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import time_util
from config import DATABASE_PATH

# SQLiteエンジンを作成し、データベースに接続
engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=True)
Session = sessionmaker(bind=engine)


def insert_random_attendance_records(num_records: int = 20):
    """ランダムな勤怠記録を挿入する"""
    with Session() as session:
        # データベース内のすべての従業員を取得
        employees = session.query(Employee).all()

        if not employees:
            print("従業員がデータベースに存在しません。")
            return

        for _ in range(num_records):
            # ランダムに従業員を選ぶ
            employee = random.choice(employees)

            # ランダムな日付を生成 (過去30日間)
            days_ago = random.randint(1, 30)
            punch_in_time = datetime.now() - timedelta(days=days_ago)

            # 出勤時間はランダムな朝9時〜11時
            punch_in_time = punch_in_time.replace(
                hour=random.randint(9, 11), minute=random.randint(0, 59)
            )

            # 勤務時間 (7〜10時間後に退勤)
            punch_out_time = punch_in_time + timedelta(hours=random.randint(7, 10))

            # 勤怠記録を作成
            attendance_in = AttendanceRecord(
                employee_id=employee.employee_id,
                record_type=RecordType.IN.name,
                record_time=punch_in_time,
                created_at=punch_in_time,
                updated_at=punch_in_time,
            )
            attendance_out = AttendanceRecord(
                employee_id=employee.employee_id,
                record_type=RecordType.OUT.name,
                record_time=punch_out_time,
                created_at=punch_out_time,
                updated_at=punch_out_time,
            )

            session.add_all([attendance_in, attendance_out])

        # コミットしてデータを保存
        session.commit()
        print(f"{num_records}件の勤怠記録が挿入されました。")


# 実行
insert_random_attendance_records(20)
