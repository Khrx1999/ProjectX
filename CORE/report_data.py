# QAReportLibrary/core/domain/report_data.py

"""
Report Data Processor
Responsible for processing test result data into structured report data
"""

from datetime import datetime
from typing import Dict, Any

from UTILS import format_datetime_thai, calculate_sprint_days, get_logger

# Setup logger
logger = get_logger("ReportData")

class ReportDataProcessor:
    """
    Process raw test result JSON data into structured report data
    """

    def prepare(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare report data from raw test results
        Args:
            test_data (Dict[str, Any]): Raw test results JSON
        
        Returns:
            Dict[str, Any]: Structured report-ready data
        """
        dashboard = test_data.get('dashboard', {})
        test_cases = test_data.get('testCases', {})

        report = {}

        # Extract dashboard information
        start_date_str = dashboard.get("START_DATE", "")
        end_date_str = dashboard.get("END_DATE", "")
        now = datetime.now()

        try:
            total_days, days_passed, days_remaining, progress_per_day = calculate_sprint_days(
                start_date_str, end_date_str, now
            )
        except Exception as e:
            logger.warning(f"Error calculating sprint days: {e}")
            total_days = days_passed = days_remaining = 0
            progress_per_day = 0.0

        # Extract test case information
        total_tc = int(test_cases.get("TOTAL", 0))
        passed_tc = int(test_cases.get("PASS", 0))
        failed_tc = int(test_cases.get("FAIL", 0))
        blocked_tc = int(test_cases.get("BLOCK", 0))
        in_progress_tc = int(test_cases.get("IN_PROGRESS", 0))
        not_started_tc = int(test_cases.get("NOT_STARTED", 0))

        # Calculate test completion progress
        completion_progress = round((passed_tc / total_tc) * 100, 1) if total_tc > 0 else 0.0
        remaining_progress = round(100 - completion_progress, 1)

        # Estimate project health (Risk Level)
        actual_progress_rate = (completion_progress / days_passed) if days_passed > 0 else 0
        expected_progress = (100 / total_days) * days_passed if total_days > 0 else 0

        days_to_completion = (remaining_progress / actual_progress_rate) if actual_progress_rate > 0 else 999
        days_difference = days_to_completion - days_remaining

        risk_level, risk_level_th, risk_level_color = self._determine_risk_level(days_difference)

        # Prepare final report data
        report.update({
            "PROJECT_NAME": dashboard.get("PROJECT_NAME", "Project Name"),
            "VERSION": dashboard.get("VERSION", "v1.0"),
            "START_DATE": self._format_date(start_date_str),
            "END_DATE": self._format_date(end_date_str),
            "TOTAL_TEST_CASES": total_tc,
            "PASSED_TEST_CASES": passed_tc,
            "FAILED_TEST_CASES": failed_tc,
            "BLOCKED_TEST_CASES": blocked_tc,
            "IN_PROGRESS_TEST_CASES": in_progress_tc,
            "NOT_STARTED_TEST_CASES": not_started_tc,
            "COMPLETION_PROGRESS": completion_progress,
            "REMAINING_PROGRESS": remaining_progress,
            "DAYS_PASSED": days_passed,
            "DAYS_REMAINING": days_remaining,
            "TOTAL_DAYS": total_days,
            "PROGRESS_PER_DAY": progress_per_day,
            "ACTUAL_PROGRESS_RATE": round(actual_progress_rate, 2),
            "EXPECTED_PROGRESS": round(expected_progress, 2),
            "DAYS_TO_COMPLETION": int(days_to_completion),
            "DAYS_DIFFERENCE": int(days_difference),
            "RISK_LEVEL": risk_level,
            "RISK_LEVEL_TH": risk_level_th,
            "RISK_LEVEL_COLOR": risk_level_color,
            "REPORT_GENERATED_TIME": format_datetime_thai(now),
        })

        return report

    def _format_date(self, date_str: str) -> str:
        """
        Format a date string (YYYY-MM-DD) to Thai formatted date
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return format_datetime_thai(dt, include_time=False)
        except Exception:
            return "N/A"

    def _determine_risk_level(self, days_difference: int) -> tuple:
        """
        Determine risk level based on days difference
        """
        if days_difference <= 0:
            return ("NONE", "ไม่มีความเสี่ยง", "text-green-500")
        elif days_difference <= 5:
            return ("LOW", "ความเสี่ยงต่ำ", "text-amber-500")
        elif days_difference <= 10:
            return ("MEDIUM", "ความเสี่ยงปานกลาง", "text-orange-500")
        elif days_difference <= 20:
            return ("HIGH", "ความเสี่ยงสูง", "text-red-500")
        else:
            return ("CRITICAL", "ความเสี่ยงวิกฤต", "text-rose-500")
