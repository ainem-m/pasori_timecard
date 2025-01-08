import sys
import json
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox,
    QLabel,
    QComboBox,
)
import config  # config.py に EMPLOYEE_LIST を設定


class MappingEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("従業員リストエディタ")
        self.resize(600, 400)

        # データを保存する辞書
        self.data = {}

        # テンプレート選択肢
        self.template_options = ["正社員", "パート", "ドクター"]

        # メインウィジェットとレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 入力エリア
        self.input_layout = QHBoxLayout()
        self.layout.addLayout(self.input_layout)

        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("従業員名")
        self.input_layout.addWidget(self.employee_input)

        self.template_input = QComboBox()
        self.template_input.addItems(self.template_options)
        self.input_layout.addWidget(self.template_input)

        self.add_button = QPushButton("追加 / 更新")
        self.add_button.clicked.connect(self.add_entry)
        self.input_layout.addWidget(self.add_button)

        # リスト表示
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(
            self.on_item_clicked
        )  # アイテムがクリックされたときに呼ばれる
        self.layout.addWidget(self.list_widget)

        # 削除ボタン
        self.delete_button = QPushButton("選択した項目を削除")
        self.delete_button.clicked.connect(self.delete_entry)
        self.layout.addWidget(self.delete_button)

        # 保存ボタン
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_data)
        self.layout.addWidget(self.save_button)

        # 終了ボタン
        self.exit_button = QPushButton("終了")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

        # 初期データ読み込み
        self.load_data()

    def add_entry(self):
        employee = self.employee_input.text().strip()
        template = self.template_input.currentText().strip()

        if not employee:
            QMessageBox.warning(self, "入力エラー", "従業員名を入力してください。")
            return

        self.data[employee] = template
        self.update_list()
        self.employee_input.clear()

    def delete_entry(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "選択エラー", "削除する項目を選択してください。")
            return

        for item in selected_items:
            employee = item.text().split(":")[0].strip()
            if employee in self.data:
                del self.data[employee]

        self.update_list()

    def update_list(self):
        self.list_widget.clear()
        for employee, template in self.data.items():
            self.list_widget.addItem(f"{employee}: {template}")

    def save_data(self):
        try:
            with open(config.EMPLOYEE_LIST, "w", encoding="utf-8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)
            QMessageBox.information(
                self, "保存完了", f"データを保存しました。\n{config.EMPLOYEE_LIST}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "保存エラー", f"データの保存に失敗しました。\n{e}"
            )

    def load_data(self):
        try:
            with open(config.EMPLOYEE_LIST, "r", encoding="utf-8") as file:
                self.data = json.load(file)
            self.update_list()
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "初期化情報",
                f"{config.EMPLOYEE_LIST} が見つかりません。新しいファイルを作成します。",
            )
            self.data = {}
        except Exception as e:
            QMessageBox.critical(
                self, "読み込みエラー", f"データの読み込みに失敗しました。\n{e}"
            )

    def on_item_clicked(self, item):
        # アイテムが選択されたときに従業員名とテンプレート名を入力欄に反映
        employee_name = item.text().split(":")[0].strip()
        template = item.text().split(":")[1].strip()

        self.employee_input.setText(employee_name)
        self.template_input.setCurrentText(template)


# アプリケーション起動
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MappingEditor()
    window.show()
    sys.exit(app.exec())
