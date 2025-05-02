"""
QAreportLibrary INFRASTRUCTURE Package
"""

from INFRASTRUCTURE.test_data_loader import TestDataLoader
from INFRASTRUCTURE.defect_data_loader import DefectDataLoader
from INFRASTRUCTURE.html_renderer import HTMLRenderer
from INFRASTRUCTURE.config import ReportConfig

config = ReportConfig()

__all__ = ["TestDataLoader", "DefectDataLoader", "config", "HTMLRenderer"] 