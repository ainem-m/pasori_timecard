import sys
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QWidget,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from db_alchemy import Employee
from config import WINDOW_SIZE


# メインのQDialogクラス
class EmployeeSelectionDialog(QDialog):
    employee_selected = Signal(Employee)  # 従業員が選択されたときに発行されるシグナル

    def __init__(self):
        super().__init__()

        self.current_page = 0
        self.employees_per_page = 6  # 1ページに表示する従業員の数
        self.employee_list = Employee.get_all()  # 従業員リストを取得
        self.total_pages = (len(self.employee_list) - 1) // self.employees_per_page + 1

        self.gui_init()

    def gui_init(self):
        self.setWindowTitle("従業員選択")
        self.resize(*WINDOW_SIZE)
        layout = QVBoxLayout(self)
        text = QLabel("登録されていないカードです。紐づける従業員を選択してください")
        layout.addWidget(text)
        # スクロール領域を設定（従業員ボタンを表示する場所）
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.button_container = QWidget()
        self.button_layout = QGridLayout(self.button_container)

        self.scroll_area.setWidget(self.button_container)
        layout.addWidget(self.scroll_area)

        # ページ移動用のボタン
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("前のページ")
        self.prev_button.clicked.connect(self.prev_page)
        self.navigation_layout.addWidget(self.prev_button)

        self.page_label = QLabel(f"Page {self.current_page + 1} of {self.total_pages}")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.navigation_layout.addWidget(self.page_label)

        self.next_button = QPushButton("次のページ")
        self.next_button.clicked.connect(self.next_page)
        self.navigation_layout.addWidget(self.next_button)

        layout.addLayout(self.navigation_layout)

        # 最後に閉じるボタン
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # 現在のページの従業員ボタンを表示
        self.update_page()

    def update_page(self):
        # 現在のページに基づいて従業員ボタンを更新
        for i in reversed(range(self.button_layout.count())):
            widget = self.button_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        start_index = self.current_page * self.employees_per_page
        end_index = start_index + self.employees_per_page
        employees_on_page = self.employee_list[start_index:end_index]

        for row, employee in enumerate(employees_on_page):
            button = QPushButton(employee.name)
            button.clicked.connect(lambda _, emp=employee: self.select_employee(emp))
            self.button_layout.addWidget(button, row // 2, row % 2)

        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")

        # ページングボタンの有効・無効を更新
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def prev_page(self):
        # 前のページへ移動
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        # 次のページへ移動
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page()

    def select_employee(self, employee):
        # 従業員が選択されたときにシグナルを発行し、ダイアログを閉じる
        self.employee_selected.emit(employee)
        self.accept()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = EmployeeSelectionDialog()
    dialog.employee_selected.connect(
        lambda emp: print(f"Selected employee: {emp.name}")
    )

    sys.exit(dialog.exec())
