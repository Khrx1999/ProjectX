"""
CORE Package

Contains core service and business logic
"""

from CORE.report_service import ReportService
from CORE.report_data import ReportDataProcessor
from CORE.defect_analyzer import analyze_defects, calculate_resolution_days, prepare_defect_analysis_data, calculate_sla_metrics, get_defect_trends
from CORE.test_summary_prepare import prepare_test_summary_data, determine_risk_level, generate_risk_recommendation
from CORE.defect_trend_prepare import prepare_defect_trend_analysis_data
# Import new prepare functions
from CORE.test_trend_prepare import prepare_test_trend_analysis_data
from CORE.module_testing_prepare import prepare_module_testing_status_data
from CORE.defect_distribution_prepare import prepare_defect_distribution_data
from CORE.defect_resolution_prepare import prepare_defect_resolution_time_data
from CORE.recent_defects_prepare import prepare_recent_defects_data

__all__ = [
    "ReportService",
    "ReportDataProcessor",
    "calculate_resolution_days",
    "prepare_defect_analysis_data",
    "calculate_sla_metrics",
    "get_defect_trends",
    "prepare_test_summary_data",
    "determine_risk_level", 
    "generate_risk_recommendation",
    "prepare_defect_trend_analysis_data",
    "prepare_test_trend_analysis_data",
    "prepare_module_testing_status_data",
    "prepare_defect_distribution_data",
    "prepare_defect_resolution_time_data",
    "prepare_recent_defects_data"
] 