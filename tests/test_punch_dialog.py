import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from pasori_timecard.punch_dialog import PunchDialog
from pasori_timecard import db_alchemy

TEST_DATE = datetime(2025, 1, 31, 9, 0)
YESTERDAY = TEST_DATE - timedelta(days=1)


class TestPunchDialog:
    @pytest.fixture(autouse=True)
    def setup_app(self, qtbot):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.qtbot = qtbot

    def create_mock_record(self, record_type, record_time=None):
        """Create a mock attendance record with controllable date"""
        mock_record = MagicMock()
        mock_record.record_type = record_type

        # Mock record_time as a MagicMock with date() support
        mock_time = MagicMock()
        target_date = (record_time or TEST_DATE).date()
        mock_time.date.return_value = target_date  # Return real date object

        mock_record.record_time = mock_time
        return mock_record

    @patch("pasori_timecard.db_alchemy.IC_Card.find_employee_by_ic_card_number")
    @patch("pasori_timecard.db_alchemy.AttendanceRecord.get_last_record")
    @patch("pasori_timecard.time_util.current_time")
    def test_initialization(
        self, mock_current_time, mock_get_last_record, mock_find_employee
    ):
        mock_find_employee.return_value = MagicMock(employee_id=1)
        mock_find_employee.return_value.name = "テスト社員"
        mock_get_last_record.return_value = self.create_mock_record(
            db_alchemy.RecordType.OUT, YESTERDAY
        )
        mock_current_time.return_value = TEST_DATE

        dialog = PunchDialog("123456", TEST_DATE)
        self.qtbot.add_widget(dialog)

        assert dialog.employee.name == "テスト社員"
        assert dialog.current_status == db_alchemy.RecordType.IN

    @patch("pasori_timecard.db_alchemy.IC_Card.find_employee_by_ic_card_number")
    @patch("pasori_timecard.db_alchemy.AttendanceRecord.get_last_record")
    def test_toggle_status_in_to_out(self, mock_get_last_record, mock_find_employee):
        mock_find_employee.return_value = MagicMock(employee_id=1, name="テスト社員")

        mock_get_last_record.return_value = self.create_mock_record(
            db_alchemy.RecordType.OUT, YESTERDAY
        )

        dialog = PunchDialog("123456", TEST_DATE)
        self.qtbot.add_widget(dialog)

        assert dialog.current_status == db_alchemy.RecordType.IN
        dialog.toggle_status()
        assert dialog.current_status == db_alchemy.RecordType.OUT

    @patch("pasori_timecard.db_alchemy.IC_Card.find_employee_by_ic_card_number")
    @patch("pasori_timecard.db_alchemy.AttendanceRecord.get_last_record")
    def test_toggle_status_out_to_in(self, mock_get_last_record, mock_find_employee):
        mock_find_employee.return_value = MagicMock(employee_id=1, name="テスト社員")
        mock_get_last_record.return_value = self.create_mock_record(
            db_alchemy.RecordType.IN, TEST_DATE
        )

        dialog = PunchDialog("123456", TEST_DATE)
        self.qtbot.add_widget(dialog)

        assert dialog.current_status == db_alchemy.RecordType.OUT
        dialog.toggle_status()
        assert dialog.current_status == db_alchemy.RecordType.IN

    @patch("pasori_timecard.db_alchemy.IC_Card.find_employee_by_ic_card_number")
    @patch("pasori_timecard.db_alchemy.AttendanceRecord.get_last_record")
    @patch("pasori_timecard.db_alchemy.AttendanceRecord.punch")
    def test_accept_records_punch(
        self, mock_punch, mock_get_last_record, mock_find_employee
    ):
        mock_find_employee.return_value = MagicMock(employee_id=1, name="テスト社員")
        mock_get_last_record.return_value = self.create_mock_record(
            db_alchemy.RecordType.IN, YESTERDAY
        )

        dialog = PunchDialog("123456", TEST_DATE)
        self.qtbot.add_widget(dialog)
        dialog.current_status = db_alchemy.RecordType.OUT

        with self.qtbot.wait_signal(dialog.accepted, timeout=1000):
            dialog.accept()

        mock_punch.assert_called_once_with(
            dialog.employee.employee_id, dialog.current_status, TEST_DATE
        )


if __name__ == "__main__":
    pytest.main([__file__])
