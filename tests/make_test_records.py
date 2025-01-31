from datetime import timedelta
import random
from pasori_timecard import db_alchemy, time_util, config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLiteエンジンを作成し、データベースに接続
engine = create_engine(f"sqlite:///{config.DATABASE_PATH}", echo=True)
Session = sessionmaker(bind=engine)


def insert_random_attendance_records(num_records: int = 20, rollback: bool = True):
    """ランダムな勤怠記録を挿入し、オプションでロールバックする"""
    with Session() as session:
        try:
            employees = session.query(db_alchemy.Employee).all()
            if not employees:
                print("従業員がデータベースに存在しません。")
                return

            for _ in range(num_records):
                employee = random.choice(employees)
                days_ago = random.randint(1, 30)
                punch_in_time = time_util.current_time() - timedelta(days=days_ago)
                punch_in_time = punch_in_time.replace(
                    hour=random.randint(9, 11), minute=random.randint(0, 59)
                )
                punch_out_time = punch_in_time + timedelta(hours=random.randint(7, 10))

                attendance_in = db_alchemy.AttendanceRecord(
                    employee_id=employee.employee_id,
                    record_type=db_alchemy.RecordType.IN.name,
                    record_time=punch_in_time,
                    created_at=punch_in_time,
                    updated_at=punch_in_time,
                )
                attendance_out = db_alchemy.AttendanceRecord(
                    employee_id=employee.employee_id,
                    record_type=db_alchemy.RecordType.OUT.name,
                    record_time=punch_out_time,
                    created_at=punch_out_time,
                    updated_at=punch_out_time,
                )

                session.add_all([attendance_in, attendance_out])

            session.commit()
            print(f"{num_records}件の勤怠記録が挿入されました。")

            if rollback:
                print("ロールバックを実行します...")
                session.rollback()
                print("ロールバックが完了しました。")

        except Exception as e:
            session.rollback()  # エラー発生時は自動でロールバック
            print(f"エラーが発生しました: {e}")


# 実行 (ロールバックあり)
insert_random_attendance_records(20, rollback=True)
