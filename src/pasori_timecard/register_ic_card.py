import db_alchemy
from nfc_reader_QThread import NfcReader
import nfc
from typing import Optional


def on_connect(tag: nfc.tag.Tag):
    ic_card_id: str = str(tag.identifier.hex())  # カードのIDを取得
    print(f"ICカードIDを読み取りました: {ic_card_id}")
    # ICカードが既に登録されているか確認
    existing_card = db_alchemy.IC_Card.find_by_ic_card_number(ic_card_id)
    if existing_card:
        print(f"このICカードID {ic_card_id} は既に登録されています。")
        return True  # 処理を終了する

    employee_name: str = input("従業員名を入力してください: ")
    employee: Optional[db_alchemy.Employee] = db_alchemy.Employee.get_by_name(
        employee_name
    )

    if not employee:
        while True:
            ans = input(
                f"従業員 {employee_name} が見つかりませんでした。登録しますか? y/n"
            )
            if ans == "y":
                db_alchemy.Employee.add(name=employee_name)
                break
            elif ans == "n":
                exit(print("終了します"))
            else:
                continue
        employee = db_alchemy.Employee.get_by_name(employee_name)
    assert employee is not None
    try:
        db_alchemy.IC_Card.assign(employee=employee, ic_card_number=ic_card_id)
        print(f"ICカードID {ic_card_id} を従業員 {employee_name} に紐づけました。")
    except Exception as e:
        print(f"ICカードの登録に失敗しました: {e}")

    return True  # 一度の接続で終了


def register(ic_card_id: str):
    employee_name: str = input("従業員名を入力してください: ")
    employee: Optional[db_alchemy.Employee] = db_alchemy.Employee.get_by_name(
        employee_name
    )
    if employee:
        try:
            db_alchemy.IC_Card.assign(employee=employee, ic_card_number=ic_card_id)
            print(f"ICカードID {ic_card_id} を従業員 {employee_name} に紐づけました。")
        except Exception as e:
            print(f"ICカードの登録に失敗しました: {e}")
            print("終了します")
            exit()
        print(f"ICカードID {ic_card_id} を従業員 {employee_name} に紐づけました。")
        exit()


if __name__ == "__main__":
    nfc_reader = NfcReader(clf=nfc.ContactlessFrontend("usb"), on_connect=on_connect)
    print("ICカードをリーダーに近づけてください")
    nfc_reader.run()
