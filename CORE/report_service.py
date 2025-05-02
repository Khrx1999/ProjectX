# QAReportLibrary/core/services/report_service.py

"""
Report Service

Core business logic for QA Report generation
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from INFRASTRUCTURE import TestDataLoader, DefectDataLoader, HTMLRenderer, config
from UTILS import get_logger, clear_cache
from CORE.report_data import ReportDataProcessor
from CORE.defect_analyzer import prepare_defect_analysis_data, calculate_sla_metrics, get_defect_trends

# Setup logger
logger = get_logger("ReportService")

class ReportService:
    """
    Core service for QA Report generation
    """
    
    def __init__(self):
        """Initialize report service"""
        self.test_data_loader = TestDataLoader()
        self.defect_data_loader = DefectDataLoader()
        self.html_renderer = HTMLRenderer()
        self.data_processor = ReportDataProcessor()
        
        self.test_data: Optional[Dict[str, Any]] = None
        self.defects_data: Optional[List[Dict[str, Any]]] = None
        self.report_data: Dict[str, Any] = {}
    
    def setup_environment(self, config_path: Optional[str] = None) -> bool:
        """
        Setup QA Report environment
        
        Args:
            config_path (Optional[str]): Path to configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If config_path is provided, load configuration
            if config_path:
                # Load configuration from file (placeholder)
                logger.info(f"Loading configuration from: {config_path}")
                
            # Initialize report data
            self.report_data = {}
            
            logger.info("QA Report environment setup successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup environment: {str(e)}")
            return False
    
    def load_test_data(self, file_path: str) -> bool:
        """
        Load test result data
        
        Args:
            file_path (str): Path to test data JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.test_data_loader.load(file_path)
            if not data:
                return False
                
            self.test_data = data
            # Process data using ReportDataProcessor
            processed_data = self.data_processor.prepare(data)
            self.report_data.update(processed_data)
            
            # Add template path to report data
            self.report_data["TEMPLATE_PATH"] = self.report_data.get("template_path", "")
            
            logger.info(f"Test data loaded successfully from: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load test data: {str(e)}")
            return False
    
    def load_defects_data(self, file_path: str) -> bool:
        """
        Load defects data
        
        Args:
            file_path (str): Path to defects data JSON file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = self.defect_data_loader.load(file_path)
            if not data:
                return False
                
            self.defects_data = data
            # Process defects data
            self._process_defects_data()
            
            logger.info(f"Defects data loaded successfully from: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load defects data: {str(e)}")
            return False
    
    def generate_report(self, output_dir: Optional[str] = None) -> str:
        """
        Generate QA Report
        
        Args:
            output_dir (Optional[str]): Output directory for the report
            
        Returns:
            str: Path to generated report
        """
        try:
            # Ensure we have minimum required data
            if not self.test_data:
                raise ValueError("No test data loaded. Call load_test_data() first.")
            
            # Prepare final report data
            self._prepare_final_report_data()
            
            # Render HTML report
            report_path = self.html_renderer.render(self.report_data, output_dir)
            
            logger.info(f"QA Report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            # Return empty string or raise exception depending on your error handling strategy
            return ""
    
    def clear_cache(self) -> None:
        """
        Clear all cached data
        """
        clear_cache()
        logger.info("Cache cleared successfully")
    
    def _process_defects_data(self) -> None:
        """
        Process defects data
        """
        if not self.defects_data:
            return
        
        # Add raw defects data to report
        self.report_data["defects_data"] = self.defects_data
        
        # Basic defect statistics from defect_analysis module
        defect_stats = prepare_defect_analysis_data(self.defects_data)
        self.report_data.update(defect_stats)
        
        # SLA metrics
        sla_data = calculate_sla_metrics(self.defects_data)
        self.report_data["sla_metrics"] = sla_data
        
        # Trend data for last 30 days
        trend_data = get_defect_trends(self.defects_data, days=30)
        self.report_data["defect_trends"] = trend_data
    
    def _prepare_final_report_data(self) -> None:
        """
        Prepare final report data before generating report
        """
        # Add timestamp
        self.report_data["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add version
        self.report_data["VERSION"] = "2.0.0"
        
        # ตรวจสอบข้อมูลทั้งหมด เพื่อป้องกันการเข้าถึง attributes ของ str objects
        for key, value in list(self.report_data.items()):
            # ถ้ามี key ที่เป็น dictionary ที่ถูกแปลงเป็น string (ซึ่งอาจจะทำให้เกิด error)
            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                try:
                    # พยายามแปลงกลับเป็น dictionary
                    dict_value = json.loads(value)
                    if isinstance(dict_value, dict):
                        self.report_data[key] = dict_value
                except (json.JSONDecodeError, ValueError):
                    # ถ้าแปลงไม่ได้ให้เก็บเป็น string ไว้
                    pass
            
            # ตรวจสอบ key ที่ชื่อ 'trendAnalysis', 'defect_analysis' หรือ 'summary'
            if key in ['trendAnalysis', 'defect_analysis', 'summary'] and isinstance(value, str):
                try:
                    # พยายามแปลงจาก JSON string เป็น object
                    dict_value = json.loads(value)
                    self.report_data[key] = dict_value
                except (json.JSONDecodeError, ValueError):
                    # ถ้าแปลงไม่ได้ให้ใช้ empty dictionary แทน
                    self.report_data[key] = {}
        
        # สร้างคลาสที่สามารถเข้าถึง dict keys เป็น attributes ได้
        class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                super(AttrDict, self).__init__(*args, **kwargs)
                self.__dict__ = self
                
        # แปลง trendAnalysis เป็น AttrDict
        if 'trendAnalysis' in self.report_data and isinstance(self.report_data['trendAnalysis'], dict):
            # แปลง trendAnalysis เป็น AttrDict
            trend_data_dict = AttrDict(self.report_data['trendAnalysis'])
            
            # เพิ่ม summary เป็น attribute
            if 'summary' in self.report_data and isinstance(self.report_data['summary'], dict):
                # ถ้ามี summary แยก ให้ใช้อันนั้น
                trend_data_dict.summary = AttrDict(self.report_data['summary'])
            else:
                # ถ้าไม่มี summary แยก ให้ใช้ค่าว่าง
                trend_data_dict.summary = AttrDict({})
                
            # อัปเดต trendAnalysis ในข้อมูลรายงาน
            self.report_data['trendAnalysis'] = trend_data_dict
