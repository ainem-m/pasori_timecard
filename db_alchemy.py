from sqlalchemy import ForeignKey, create_engine, desc
from sqlalchemy.orm import (
    DeclarativeBase,
    mapped_column,
    Mapped,
    relationship,
    sessionmaker,
)
from datetime import datetime
import enum
from config import DATABASE_PATH, DEBUG, EMPLOYEE_LIST
from typing import Any, Optional
import time_util
import os


engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
Session = sessionmaker(bind=engine)


class RecordType(enum.Enum):
    IN = "出勤"
    OUT = "退勤"


class Base(DeclarativeBase):
    pass


class Employee(Base):
    """
    CREATE TABLE IF NOT EXISTS Employee (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """

    __tablename__ = "Employee"

    employee_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    ic_cards = relationship("IC_Card", back_populates="employee")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")

    @classmethod
    def get_all(cls):
        with Session() as session:
            return session.query(cls).all()

    @classmethod
    def get_by_name(cls: Any, name: str) -> Optional[Any]:
        with Session() as session:
            return session.query(cls).filter_by(name=name).first()

    def ic_card_list(self):
        # employee_idに紐づけられているIC_Cardのリストを返す
        id = self.employee_id
        with Session() as session:
            return session.query(IC_Card).filter_by(employee_id=id).all()

    @classmethod
    def add(cls, name: str):
        with Session() as session:
            existing_employee = session.query(cls).filter_by(name=name).first()
            if existing_employee is None:
                # 従業員が存在しない場合、新しい従業員を追加
                new_employee = cls(
                    name=name,
                    created_at=time_util.current_time(),
                    updated_at=time_util.current_time(),
                )
                session.add(new_employee)
                session.commit()
                print(f"新しい従業員 '{name}' が追加されました。")
            else:
                print(f"従業員 '{name}' はすでに存在しています。")

    def __repr__(self):
        return (
            f"Employee(employee_id={self.employee_id}, name='{self.name}', "
            f"created_at=datetime.fromisoformat('{self.created_at}'), updated_at=datetime.fromisoformat('{self.updated_at}'))"
        )


class IC_Card(Base):
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

    __tablename__ = "IC_Card"

    card_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey(Employee.employee_id))
    ic_card_number: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    employee = relationship("Employee", back_populates="ic_cards")

    @classmethod
    def get_all(cls):
        with Session() as session:
            return session.query(cls).all()

    @classmethod
    def assign(cls: Any, ic_card_number: str, employee: Employee):
        with Session() as session:
            # IC_Cardがすでに存在するか確認
            existing_ic_card = (
                session.query(cls).filter_by(ic_card_number=ic_card_number).first()
            )
            if existing_ic_card is not None:
                # カードが既に登録されている場合、従業員との紐づけを変更する
                old_employee_id = existing_ic_card.employee_id
                existing_ic_card.employee_id = employee.employee_id
                existing_ic_card.updated_at = time_util.current_time()
                print(
                    f"{old_employee_id}と紐づけられていたICカード'{ic_card_number}' は {employee.name}に紐づけされました。"
                )
            else:
                # 新しいIC_Cardを作成し、従業員と紐づける
                new_ic_card = cls(
                    ic_card_number=ic_card_number,
                    employee_id=employee.employee_id,
                    created_at=time_util.current_time(),
                    updated_at=time_util.current_time(),
                )
                session.add(new_ic_card)
                print(
                    f"ICカード'{ic_card_number}'は{employee.name}に紐づけされました。"
                )

            # 変更をコミット
            session.commit()

    @classmethod
    def find_by_ic_card_number(cls: Any, ic_card_number: str):
        with Session() as session:
            return session.query(cls).filter_by(ic_card_number=ic_card_number).first()

    @classmethod
    def find_employee_by_ic_card_number(
        cls: Any, ic_card_number: str
    ) -> Optional[Employee]:
        """ICカードナンバーと紐づけられた従業員のレコードを返す

        Args:
            cls (IC_Card): なんでAnyにしなければならないんだ…
            ic_card_number (str)

        Returns:
            Optional[Employee]
        """
        with Session() as session:
            ic_card = (
                session.query(cls).filter_by(ic_card_number=ic_card_number).first()
            )
            if ic_card is None:
                print(
                    f"ICカード'{ic_card_number}'がテーブルIC_Cardの中にみつかりません"
                )
                return None
            employee_id: int = ic_card.employee_id
            return session.query(Employee).filter_by(employee_id=employee_id).first()

    def __repr__(self):
        return (
            f"IC_Card(card_id={self.card_id}, employee_id={self.employee_id}, ic_card_number='{self.ic_card_number}', "
            f"created_at=datetime.fromisoformat('{self.created_at}'), updated_at=datetime.fromisoformat('{self.updated_at}'))"
        )


class AttendanceRecord(Base):
    """
    CREATE TABLE IF NOT EXISTS AttendanceRecord (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        record_type TEXT NOT NULL CHECK (record_type IN ('IN', 'OUT')),
        record_time TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(employee_id) REFERENCES Employee(employee_id)
    )
    """

    __tablename__ = "AttendanceRecord"

    record_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey(Employee.employee_id))
    record_type: Mapped[RecordType]
    record_time: Mapped[datetime]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    employee = relationship("Employee", back_populates="attendance_records")

    @classmethod
    def get_all(cls):
        with Session() as session:
            return session.query(cls).all()

    @classmethod
    def get_last_record(cls: Any, employee: Employee):
        with Session() as session:
            return (
                session.query(cls)
                .filter_by(employee_id=employee.employee_id)
                .order_by(desc(cls.record_time))
                .first()
            )

    @classmethod
    def punch(
        cls: Any, employee_id: int, record_type: RecordType, punch_time: datetime
    ):
        with Session() as session:
            new_record = cls(
                employee_id=employee_id,
                record_type=record_type.name,
                record_time=punch_time,
                created_at=punch_time,
                updated_at=punch_time,
            )
            session.add(new_record)
            session.commit()
            print(f"記録しました{new_record}")

    def __repr__(self):
        return (
            f"AttendanceRecord(record_id={self.record_id}, employee_id={self.employee_id}, record_type='{self.record_type}', "
            f"record_time=datetime.fromisoformat('{self.record_time}'), "
            f"created_at=datetime.fromisoformat('{self.created_at}'), updated_at=datetime.fromisoformat('{self.updated_at}'))"
        )

    def __str__(self):
        return f"AttendanceRecord: {time_util.datetime_to_string(self.record_time)}{self.record_type.value} {self.employee_id}"


if __name__ == "__main__":
    # データベースの初期化
    Base.metadata.create_all(engine)

    # EMPLOYEE_LISTに書かれている従業員名が登録されていなかったら登録する
    if os.path.exists(EMPLOYEE_LIST):
        employee_names: list[str] = list(map(lambda x: x.name, Employee.get_all()))
        with open(EMPLOYEE_LIST, "r+", encoding="utf-8") as file:
            for line in file:
                employee_name = line.strip()  # 改行を削除して従業員名を取得
                Employee.add(
                    employee_name
                )  # もし従業員がすでに存在した場合のエラーハンドリングはEmployee側に任せる
            # EMPLOYEE_LISTに従業員名を同期する
            # データベースの従業員リストに同期するため、EMPLOYEE_LISTを上書き更新
            file.seek(0)  # ファイルの先頭に戻る
            file.truncate()  # ファイル内容を削除
            # データベースに存在する従業員名をすべて書き込む
            for employee in Employee.get_all():
                file.write(f"{employee.name}\n")
            print("従業員リストをファイルに同期しました。")
