import sqlite3
from datetime import datetime

import time_util
from config import DATABASE_PATH, RecordType
from typing import Optional, NamedTuple, Generator

# TODO strをidとかdatetimeとかに意味をもたせる？


class Employee(NamedTuple):
    employee_id: str
    name: str
    created_at: str
    updated_at: str


class IC_Card(NamedTuple):
    card_id: str
    employee_id: str
    ic_card_number: str
    created_at: str
    updated_at: str


class AttendanceRecord(NamedTuple):
    record_id: str
    employee_id: str
    record_type: RecordType
    record_time: str
    created_at: str
    updated_at: str


# データベースに接続
def connect_db():
    return sqlite3.connect(DATABASE_PATH)


# データベースの初期化
def initialize_db():
    conn = connect_db()
    cursor = conn.cursor()

    # テーブルの作成
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Employee (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS IC_Card (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            ic_card_number TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES Employee(employee_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS AttendanceRecord (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            record_type TEXT NOT NULL CHECK (record_type IN ('出勤', '退勤')),
            record_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES Employee(employee_id)
        )
    """
    )

    conn.commit()
    conn.close()


# 従業員をデータベースに追加
def insert_employee(name):
    conn = connect_db()
    cursor = conn.cursor()

    now = time_util.datetime_to_string(time_util.current_time())
    cursor.execute(
        """
        INSERT INTO Employee (name, created_at, updated_at)
        VALUES (?, ?, ?)
    """,
        (name, now, now),
    )

    conn.commit()
    conn.close()


# ICカードを従業員に紐づけて追加
def insert_ic_card(employee_id, ic_card_number):
    conn = connect_db()
    cursor = conn.cursor()

    now = time_util.datetime_to_string(time_util.current_time())
    cursor.execute(
        """
        INSERT INTO IC_Card (employee_id, ic_card_number, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """,
        (employee_id, ic_card_number, now, now),
    )

    conn.commit()
    conn.close()


# 出勤または退勤のレコードをデータベースに挿入
def insert_record(employee_id: str, record_type: RecordType, punch_time: datetime):
    conn = connect_db()
    cursor = conn.cursor()
    punch_time_iso = time_util.datetime_to_string(punch_time)

    # TODO データベースも修正必要？
    cursor.execute(
        """
        INSERT INTO AttendanceRecord (employee_id, record_type, record_time, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            employee_id,
            record_type.value,
            punch_time_iso,
            punch_time_iso,
            punch_time_iso,
        ),
    )
    print(employee_id, record_type.name, punch_time_iso)
    conn.commit()
    conn.close()


# ICカード番号から従業員を検索
def get_employee_by_ic_card(ic_card_id) -> Optional[Employee]:
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT Employee.*
        FROM Employee
        JOIN IC_Card ON Employee.employee_id = IC_Card.employee_id
        WHERE IC_Card.ic_card_number = ?
    """,
        (ic_card_id,),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return Employee(*result)
    else:
        return None


def get_employee_by_name(name) -> Optional[Employee]:
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM Employee WHERE name = ?
    """,
        (name,),
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return Employee(*result)
    else:
        return None


def get_ic_card_by_id(ic_card_id: str) -> Optional[IC_Card]:
    """
    指定されたICカード番号に対応するレコードをIC_Cardテーブルから取得

    Parameters:
    ----------
    ic_card_id : str
        検索するICカード番号。

    Returns:
    -------
    tuple or None
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM IC_Card WHERE ic_card_number = ?", (ic_card_id,))
    result = cursor.fetchone()
    conn.close()
    return IC_Card(*result)


def get_ic_card_by_employee_id(
    employee_id: str,
) -> Generator[Optional[IC_Card], None, bool]:
    conn = connect_db()
    cursor = conn.cursor()

    # SQLクエリで複数の結果を取得
    cursor.execute("SELECT * FROM IC_Card WHERE employee_id = ?", (employee_id,))
    results = cursor.fetchall()  # 全ての結果を取得

    conn.close()

    # 取得したレコードを1つずつIC_Cardに変換し、yieldで返す
    if results:
        for result in results:
            yield IC_Card(*result)  # 1つのレコードごとにIC_Cardを生成して返す
    else:
        yield None  # 該当するレコードがない場合

    return True  # 最後にTrueを返す


# 最後の出勤・退勤記録を取得
def get_last_record(employee_id: str) -> Optional[AttendanceRecord]:
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM AttendanceRecord
        WHERE employee_id = ?
        ORDER BY record_time DESC
        LIMIT 1
    """,
        (employee_id,),
    )

    result = cursor.fetchone()
    conn.close()
    print("###get_last_record", result)
    if result:
        # record_typeをstrからrecord_typeにしたい
        try:
            result[2] = RecordType[result[2]]
        except KeyError as e:
            print("KeyErrorしてる", e)
            if result[2] == RecordType.IN.value:
                print("？？shukkin", result[2])
                result[2] = RecordType.IN
            elif result[2] == RecordType.OUT.value:
                print("？？taikin", result[2])
                result[2] = RecordType.OUT
            else:
                print("？？", result[2])
        return AttendanceRecord(*result)
    else:
        return None


if __name__ == "__main__":
    # データベースの初期化
    initialize_db()
