from robot.api import logger
from robot.api.deco import keyword
import os
import json
from datetime import datetime
import sys
import platform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from CORE.report_service import ReportService
from CORE.metrics_calculator import calculate_test_metrics, calculate_defect_metrics
from CORE.defect_analyzer import analyze_defects, prepare_defect_analysis_data, calculate_sla_metrics, get_defect_trends
from CORE.test_summary_prepare import prepare_test_summary_data, determine_risk_level, generate_risk_recommendation
from CORE.defect_trend_prepare import prepare_defect_trend_analysis_data
from CORE.test_trend_prepare import prepare_test_trend_analysis_data
from CORE.module_testing_prepare import prepare_module_testing_status_data
from CORE.defect_distribution_prepare import prepare_defect_distribution_data
from CORE.defect_resolution_prepare import prepare_defect_resolution_time_data
from CORE.recent_defects_prepare import prepare_recent_defects_data

# Import infrastructure modules
from INFRASTRUCTURE.test_data_loader import TestDataLoader
from INFRASTRUCTURE.defect_data_loader import DefectDataLoader
from INFRASTRUCTURE.html_renderer import HTMLRenderer

# Import utilities
from UTILS.utils import get_logger, setup_logging
from UTILS import format_datetime_thai, calculate_sprint_days, clear_cache

# Import TemplateFinder
from TemplateFinder import TemplateFinder

class QAReportLibrary2:
    """
    QA Report Library for Robot Framework
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    
    def __init__(self):
        self.data_cache = {}
        self.defect_cache = {}
        self.template_cache = {}
        self.report_data = {}
        

        self.report_data_test_summary = {}
        self.report_data_defect_trend = {}
        self.report_data_test_trend = {}
        self.report_data_module_status = {}
        self.report_data_defect_distribution = {}
        self.report_data_resolution_time = {}
        self.report_data_recent_defects = {}
        
        self.library_path = os.path.dirname(os.path.abspath(__file__))
        
        self.setup_logging()
        self.logger = get_logger("QAReportLibrary")
        self.logger.info(f"QAReportLibrary initialized from: {self.library_path}")
        
        self.report_service = ReportService()
        self.test_data_loader = TestDataLoader()
        self.defect_data_loader = DefectDataLoader()
        self.html_renderer = HTMLRenderer()
        
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.template_name = None
        self.data_file = None
        self.defects_file = None 
        self.output_dir = None
        self.test_data = None
        self.defects_data = []

    def setup_logging(self, log_level: str = "INFO", log_to_file: bool = True) -> None:
        log_dir = os.path.join(os.path.dirname(self.library_path), "LOG")
        os.makedirs(log_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file_path = os.path.join(log_dir, f"qa_report_{today}.log")
        
        setup_logging(log_level=log_level, log_to_file=log_to_file, log_file_path=log_file_path)
        
        if not hasattr(self, '_logging_setup_done'):
            logger = get_logger("QAReportLibrary.Setup")
            logger.info(f"Logging setup complete. Log file: {log_file_path if log_to_file else 'None'}")
            self._logging_setup_done = True

    @keyword("Setup QA Report")
    def setup_qa_report(self, data_file: str, template_path: str, output_dir: str, defects_file: str = None) -> dict:
        logger = get_logger("QAReportLibrary.Setup")
        log_file_path = os.path.abspath(
            os.path.join(os.path.dirname(self.library_path), "LOG",
                         f"qa_report_{datetime.now().strftime('%Y-%m-%d')}.log")
        )
        logger.info("📦 [SYSTEM] Logging Initialized")
        logger.info(f"\n• Log File: {log_file_path}\n")
        logger.info('────────────────────────────────────────────────────────────────────')
        logger.info("🛠 [SETUP] QA Report Environment")
        logger.info(f"➤ Data Source: {os.path.abspath(data_file)}")
        if defects_file:
            logger.info(f"➤ Defect Source: {os.path.abspath(defects_file)}")
        else:
            logger.info("➤ Defect Source: (None Provided)")        
        logger.info(f"➤ Template File: {os.path.abspath(template_path)}")
        logger.info(f"➤ Output Directory: {os.path.abspath(output_dir)}")
        if not os.path.exists(data_file):
            logger.error(f"[ERROR] Data file not found: {data_file}")
            logger.info('────────────────────────────────────────────────────────────────────')
            raise FileNotFoundError(f"Data file not found: {data_file}")
            
        if not os.path.exists(template_path):
            logger.error(f"[ERROR] Template file not found: {template_path}")
            logger.info('────────────────────────────────────────────────────────────────────')
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        if defects_file and not os.path.exists(defects_file):
            logger.warning(f"⚠️ [WARN] Defects file not found: {defects_file}")
        
        # 4. Output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # 5. เก็บข้อมูลลงในตัวแปรของ class
        self.data_file = data_file
        self.defects_file = defects_file
        self.template_name = template_path
        self.output_dir = output_dir
        
        # 6. โหลดข้อมูล Test
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
            logger.info("Test data loaded successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to load test data: {str(e)}")
            logger.info('────────────────────────────────────────────────────────────────────')
            raise Exception(f"Failed to load test data: {str(e)}")
        
        # 7. โหลดข้อมูล Defect (ถ้ามี)
        if defects_file:
            try:
                with open(defects_file, 'r', encoding='utf-8') as f:
                    defects_content = json.load(f)
                    
                # ตรวจสอบรูปแบบข้อมูล defects
                if isinstance(defects_content, dict) and "defects" in defects_content:
                    self.defects_data = defects_content["defects"]
                elif isinstance(defects_content, list):
                    self.defects_data = defects_content
                else:
                    self.defects_data = []
                    
                logger.info(f"Defects data loaded successfully. Total: {len(self.defects_data)} defects")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load defects data: {str(e)}")
                self.defects_data = []
        
        # 8. ตั้งค่าข้อมูลสำหรับ report
        self.report_data = {
            "TEMPLATE_PATH": template_path,
            "OUTPUT_DIR": output_dir,
            "ENVIRONMENT_INFO": {
                "PYTHON_VERSION": platform.python_version(),
                "SYSTEM": platform.system(),
                "PROCESSOR": platform.processor(),
                "REPORT_GENERATED_TIME": format_datetime_thai(datetime.now())
            }
        }
        
        logger.info("Environment Setup: Complete\n")
        logger.info('────────────────────────────────────────────────────────────────────')
        
        return {
            "status": "success",
            "data_file": data_file,
            "template_path": template_path,
            "output_dir": output_dir,
            "defects_file": defects_file
        }
    
    @keyword("Prepare Test Summary Data")
    def prepare_test_summary_data(self, data_file: str = None) -> dict:
        logger = get_logger("QAReportLibrary.TestSummary")
        data_file = data_file or self.data_file
        if not data_file:
            logger.error("No data file provided for Test Summary Data preparation")
            return {}
        
        logger.info(f"Preparing Test Summary Data from: {os.path.abspath(data_file)}")
        
        if not os.path.exists(data_file):
            logger.error(f"Data file not found: {data_file}")
            return {}
        
        if not self.test_data:
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.test_data = json.load(f)
                logger.info(f"Test data loaded successfully from: {data_file}")
            except Exception as e:
                logger.error(f"Failed to load test data: {str(e)}")
                return {}
        
        try:
            # เก็บข้อมูลใน self.report_data_test_summary แทนที่ self.report_data
            self.report_data_test_summary = prepare_test_summary_data(self.test_data, data_file)
            
            # อัพเดทข้อมูลสำหรับ report โดยรวม (ยังคงความเข้ากันได้กับโค้ดเดิม)
            self.report_data.update(self.report_data_test_summary)
            
            logger.info("Test Summary Data prepared successfully")
            logger.info(f"  TOTAL_TEST_CASES: {self.report_data_test_summary.get('TOTAL_TEST_CASES', 0)}")
            logger.info(f"  PASSED_TEST_CASES: {self.report_data_test_summary.get('PASSED_TEST_CASES', 0)}")
            logger.info(f"  FAILED_TEST_CASES: {self.report_data_test_summary.get('FAILED_TEST_CASES', 0)}")
            logger.info(f"  BLOCKED_TEST_CASES: {self.report_data_test_summary.get('BLOCKED_TEST_CASES', 0)}")
            logger.info(f"  IN_PROGRESS_TEST_CASES: {self.report_data_test_summary.get('IN_PROGRESS_TEST_CASES', 0)}")
            logger.info(f"  NOT_STARTED_TEST_CASES: {self.report_data_test_summary.get('NOT_STARTED_TEST_CASES', 0)}")
            logger.info(f"  PASS_RATE: {self.report_data_test_summary.get('PASS_RATE', 0)}%")
            logger.info(f"  COMPLETION_PROGRESS: {self.report_data_test_summary.get('COMPLETION_PROGRESS', 0)}%")
            logger.info(f"  RISK_LEVEL: {self.report_data_test_summary.get('RISK_LEVEL', 'UNKNOWN')}")
            
            return self.report_data_test_summary
        except Exception as e:
            logger.error(f"Error preparing Test Summary Data: {str(e)}")
            return {}
    
    @keyword("Prepare Defect Trend Analysis Data")
    def prepare_defect_trend_analysis_data(self, defects_file: str = None) -> dict:
        """
        เตรียมข้อมูลแนวโน้มข้อบกพร่องสำหรับ QA Report
        
        Args:
            defects_file (str, optional): ที่อยู่ของไฟล์ข้อมูลข้อบกพร่อง (JSON) หากไม่ระบุจะใช้ที่ตั้งค่าไว้จาก Setup QA Report
        
        Returns:
            dict: ข้อมูลแนวโน้มข้อบกพร่อง
        """
        logger = get_logger("QAReportLibrary.DefectTrend")
        
        # ใช้ defects_file ที่รับเข้ามา หรือใช้ค่าที่ตั้งไว้ใน setup
        defects_file = defects_file or self.defects_file
        if not defects_file:
            logger.warning("⚠️ No defects file provided for Defect Trend Analysis preparation")
            return {}
        
        # แสดงข้อมูลเริ่มต้น
        logger.info(f"⏳ Preparing Defect Trend Analysis Data from: {os.path.abspath(defects_file)}")
        
        # ตรวจสอบไฟล์
        if not os.path.exists(defects_file):
            logger.error(f"Defects file not found: {defects_file}")
            return {}
        
        # โหลดข้อมูลถ้ายังไม่มี
        if not self.defects_data:
            try:
                with open(defects_file, 'r', encoding='utf-8') as f:
                    defects_content = json.load(f)
                    
                # ตรวจสอบรูปแบบข้อมูล defects
                if isinstance(defects_content, dict) and "defects" in defects_content:
                    self.defects_data = defects_content["defects"]
                elif isinstance(defects_content, list):
                    self.defects_data = defects_content
                else:
                    self.defects_data = []
                    
                logger.info(f"Defects data loaded successfully from: {defects_file} ({len(self.defects_data)} defects)")
            except Exception as e:
                logger.error(f"Failed to load defects data: {str(e)}")
                return {}
        
        # เตรียมข้อมูล Defect Trend
        try:
            # เก็บข้อมูลในตัวแปรเฉพาะ
            self.report_data_defect_trend = prepare_defect_trend_analysis_data(self.defects_data)
            
            # บันทึกข้อมูลลงใน report_data (ยังคงความเข้ากันได้กับโค้ดเดิม)
            self.report_data.update(self.report_data_defect_trend)
            
            # แสดงข้อมูลสรุป
            logger.info("Defect Trend Analysis Data prepared successfully")
            logger.info(f"  TOTAL_DEFECTS: {self.report_data_defect_trend.get('TOTAL_DEFECTS', 0)}")
            logger.info(f"  TOTAL_DEFECTS_OPEN: {self.report_data_defect_trend.get('TOTAL_DEFECTS_OPEN', 0)}")
            logger.info(f"  TOTAL_DEFECTS_CLOSED: {self.report_data_defect_trend.get('TOTAL_DEFECTS_CLOSED', 0)}")
            logger.info(f"  TOTAL_DEFECTS_CLOSED_PERCENT: {self.report_data_defect_trend.get('TOTAL_DEFECTS_CLOSED_PERCENT', 0)}%")
            logger.info(f"  AVG_FIX_TIME_DAYS: {self.report_data_defect_trend.get('AVG_FIX_TIME_DAYS', 0)}")
            logger.info(f"  DEFECT_CLOSURE_RATE: {self.report_data_defect_trend.get('DEFECT_CLOSURE_RATE', 0)} per day")
            logger.info(f"  PEAK_DEFECT_DATE: {self.report_data_defect_trend.get('PEAK_DEFECT_DATE', 'N/A')} ({self.report_data_defect_trend.get('PEAK_DEFECT_COUNT', 0)} defects)")
            
            return self.report_data_defect_trend
        except Exception as e:
            logger.error(f"Error preparing Defect Trend Analysis Data: {str(e)}")
            return {}
    
    @keyword("Prepare Test Trend Analysis Data")
    def prepare_test_trend_analysis_data(self, data_file: str = None, defects_file: str = None) -> dict:
        logger = get_logger("QAReportLibrary.TestTrend")
        
        test_data_path = os.path.abspath(data_file) if data_file else self.data_file
        defect_data_path = os.path.abspath(defects_file) if defects_file else self.defects_file

        logger.info(f"Preparing Test Trend Analysis Data from: {test_data_path}")
        if defect_data_path:
            logger.info(f"With defect data from: {defect_data_path}")

        if not self.test_data or test_data_path != self.data_file:
            self.test_data = self.test_data_loader.load(test_data_path)
            self.data_file = test_data_path
            logger.info(f"Test data loaded successfully from: {test_data_path}")
            
        defects_data = None
        if defect_data_path:
            defects_data = self.defect_data_loader.load(defect_data_path)
            logger.info(f"Defect data loaded successfully for Test Trend Analysis")

        try:
            self.report_data_test_trend = prepare_test_trend_analysis_data(self.test_data, defects_data)

            self.report_data.update(self.report_data_test_trend)
            
            logger.info("Test Trend Analysis Data prepared successfully")
            return self.report_data_test_trend
        except Exception as e:
            logger.error(f"Error preparing Test Trend Analysis Data: {str(e)}")
            return {}
    
    @keyword("Prepare Module Testing Status Data")
    def prepare_module_testing_status_data(self, data_file: str = None) -> dict:
        """
        ***| Description |***
        - Keyword สำหรับเตรียมข้อมูล Module Testing Status โดยเฉพาะ
        - แสดงสถานะการทดสอบแยกตามโมดูล

        ***| Example |***
        | ${module_status}= | *`Prepare Module Testing Status Data`* | data_file=path/to/test_data.json |

        ***| Parameters |***
        - **`data_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Test Results

        ***| Returns |***
        - **`dict`**: Dictionary ที่มีข้อมูล Module Testing Status พร้อมสำหรับใช้ใน Template

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            if not self.test_data:
                logger.warning("⚠️ Test data not loaded. Calling Prepare Test Summary Data first.")
                summary_result = self.prepare_test_summary_data(data_file)
                if not summary_result:
                    return {}
                    
            # เรียกใช้ฟังก์ชันจาก CORE/module_testing_prepare.py
            module_status_data = prepare_module_testing_status_data(self.test_data)
            
            # อัพเดท report_data
            self.report_data.update(module_status_data)
            
            return module_status_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการเตรียม Module Testing Status Data: {str(e)}")
            return {}
    
    @keyword("Prepare Defect Distribution Data")
    def prepare_defect_distribution_data(self, defects_file: str = None) -> dict:
        """
        ***| Description |***
        - Keyword สำหรับเตรียมข้อมูล Defect Distribution โดยเฉพาะ
        - วิเคราะห์การกระจายตัวของข้อบกพร่อง

        ***| Example |***
        | ${defect_distribution}= | *`Prepare Defect Distribution Data`* | defects_file=path/to/defects.json |

        ***| Parameters |***
        - **`defects_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects

        ***| Returns |***
        - **`dict`**: Dictionary ที่มีข้อมูล Defect Distribution พร้อมสำหรับใช้ใน Template

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            if not self.defects_data:
                 logger.warning("⚠️ Defects data not loaded. Calling Prepare Defect Trend Analysis Data first.")
                 trend_result = self.prepare_defect_trend_analysis_data(defects_file)
                 # ไม่จำเป็นต้องเช็คผลลัพธ์ เพราะ prepare_defect_trend_analysis_data จะสร้าง self.defects_data = [] ถ้าโหลดไม่ได้
            
            # เรียกใช้ฟังก์ชันจาก CORE/defect_distribution_prepare.py
            defect_distribution_data = prepare_defect_distribution_data(self.defects_data)
            
            # อัพเดท report_data
            self.report_data.update(defect_distribution_data)
            
            return defect_distribution_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการเตรียม Defect Distribution Data: {str(e)}")
            return {}
    
    @keyword("Prepare Defect Resolution Time Data")
    def prepare_defect_resolution_time_data(self, defects_file: str = None) -> dict:
        """
        ***| Description |***
        - Keyword สำหรับเตรียมข้อมูล Defect Resolution Time โดยเฉพาะ
        - วิเคราะห์เวลาที่ใช้ในการแก้ไขข้อบกพร่อง

        ***| Example |***
        | ${resolution_time}= | *`Prepare Defect Resolution Time Data`* | defects_file=path/to/defects.json |

        ***| Parameters |***
        - **`defects_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects

        ***| Returns |***
        - **`dict`**: Dictionary ที่มีข้อมูล Defect Resolution Time พร้อมสำหรับใช้ใน Template

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            if not self.defects_data:
                logger.warning("⚠️ Defects data not loaded. Calling Prepare Defect Trend Analysis Data first.")
                self.prepare_defect_trend_analysis_data(defects_file)

            # เรียกใช้ฟังก์ชันจาก CORE/defect_resolution_prepare.py
            resolution_time_data = prepare_defect_resolution_time_data(self.defects_data)
            
            # อัพเดท report_data
            self.report_data.update(resolution_time_data)
            
            return resolution_time_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการเตรียม Defect Resolution Time Data: {str(e)}")
            return {}    
        
    @keyword("Prepare Recent Defects Data")
    def prepare_recent_defects_data(self, defects_file: str = None) -> dict:
        """
        ***| Description |***
        - Keyword สำหรับเตรียมข้อมูล Recent Defects โดยเฉพาะ
        - แสดงข้อบกพร่องล่าสุดพร้อมรายละเอียด

        ***| Example |***
        | ${recent_defects}= | *`Prepare Recent Defects Data`* | defects_file=path/to/defects.json |

        ***| Parameters |***
        - **`defects_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects

        ***| Returns |***
        - **`dict`**: Dictionary ที่มีข้อมูล Recent Defects พร้อมสำหรับใช้ใน Template

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            if not self.defects_data:
                logger.warning("⚠️ Defects data not loaded. Calling Prepare Defect Trend Analysis Data first.")
                self.prepare_defect_trend_analysis_data(defects_file)

            # เรียกใช้ฟังก์ชันจาก CORE/recent_defects_prepare.py ใช้ limit = len(self.defects_data) เพื่อโชว์ทั้งหมด
            limit = len(self.defects_data) if self.defects_data else 0
            recent_defects_data = prepare_recent_defects_data(self.defects_data, limit=limit)
            
            # อัพเดท report_data
            self.report_data.update(recent_defects_data)
            
            return recent_defects_data
            
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการเตรียม Recent Defects Data: {str(e)}")
            return {}
        
    @keyword("Prepare Report Data")
    def prepare_report_data(self, data_file: str = None, defects_file: str = None) -> dict:
        """
        ***| Description |***
        - Keyword สำหรับเตรียมข้อมูลรายงาน QA ทั้งหมดในครั้งเดียว
        - รวมทุกส่วนของข้อมูลที่จำเป็นสำหรับรายงาน ครบทั้ง Test/Defect (7 prepares)

        ***| Example |***
        | ${report_data}= | *`Prepare Report Data`* | data_file=path/to/test_data.json | defects_file=path/to/defects.json |

        ***| Parameters |***
        - **`data_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Test Results
        - **`defects_file`** (`str`, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects

        ***| Returns |***
        - **`dict`**: Dictionary ที่มีข้อมูลทั้งหมดสำหรับรายงาน

        ***| Create By |***
        | *`Tassana Khrueawan`* | (Revised by AI for full orchestration)
        """
        logger.info("⏳ เริ่มต้นเตรียมข้อมูลรายงาน QA (ทุก prepare)...")
        # ใช้ paths จาก parameter หรือใช้ค่าที่ตั้งไว้ใน Setup
        data_path = os.path.abspath(data_file) if data_file else self.data_file
        defects_path = os.path.abspath(defects_file) if defects_file else self.defects_file

        # --- 1. เตรียมข้อมูล Test Summary ---
        logger.info("--- Prepare Test Summary Data ---")
        test_summary = self.prepare_test_summary_data(data_path)
        self.report_data.update(test_summary or {})

        # --- 2. เตรียมข้อมูล Defect Trend Analysis ---
        logger.info("--- Prepare Defect Trend Analysis Data ---")
        defect_trend = self.prepare_defect_trend_analysis_data(defects_path)
        self.report_data.update(defect_trend or {})

        # --- 3. เตรียมข้อมูล Test Trend Analysis ---
        logger.info("--- Prepare Test Trend Analysis Data ---")
        test_trend = self.prepare_test_trend_analysis_data(data_path, defects_path)
        self.report_data.update(test_trend or {})

        # --- 4. เตรียมข้อมูล Module Testing Status ---
        logger.info("--- Prepare Module Testing Status Data ---")
        module_status = self.prepare_module_testing_status_data(data_path)
        self.report_data.update(module_status or {})

        # --- 5. เตรียมข้อมูล Defect Distribution ---
        logger.info("--- Prepare Defect Distribution Data ---")
        defect_dist = self.prepare_defect_distribution_data(defects_path)
        self.report_data.update(defect_dist or {})

        # --- 6. เตรียมข้อมูล Defect Resolution Time ---
        logger.info("--- Prepare Defect Resolution Time Data ---")
        defect_reso = self.prepare_defect_resolution_time_data(defects_path)
        self.report_data.update(defect_reso or {})

        # --- 7. เตรียมข้อมูล Recent Defects ---
        logger.info("--- Prepare Recent Defects Data ---")
        recent_defects = self.prepare_recent_defects_data(defects_path)
        self.report_data.update(recent_defects or {})

        # --- ข้อมูลเพิ่มเติม ---
        self.report_data["REPORT_GENERATED_TIME"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return self.report_data

    def _generate_with_html_renderer(self, output_file: str) -> str:
        logger = get_logger("QAReportLibrary.HTMLRenderer")
        
        # Prepare template directory and filename
        template_dir = os.path.dirname(self.template_name)
        template_file = os.path.basename(self.template_name)
        
        # Setup HTML Renderer
        self.html_renderer._setup_environment(template_dir)
        
        # เตรียมข้อมูลทั้งหมดสำหรับเทมเพลต
        template_data = self.report_data.copy()
        
        # แสดงข้อมูลสำคัญก่อนการ render
        logger.info(f"🔍 ตรวจสอบข้อมูลก่อนการ render:")
        logger.info(f"  TOTAL_TEST_CASES: {template_data.get('TOTAL_TEST_CASES')}")
        logger.info(f"  PASSED_TEST_CASES: {template_data.get('PASSED_TEST_CASES')}")
        
        # เพิ่มข้อมูลเฉพาะส่วนเข้าไปใน template_data เพื่อให้แน่ใจว่ามีข้อมูลล่าสุด
        if self.report_data_test_summary:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ test_summary.html ({len(self.report_data_test_summary)} keys)")
            template_data.update(self.report_data_test_summary)
        if self.report_data_test_trend:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ test_trend_analysis.html ({len(self.report_data_test_trend)} keys)")
            template_data.update(self.report_data_test_trend)
        if self.report_data_defect_distribution:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ defect_distribution.html ({len(self.report_data_defect_distribution)} keys)")
            template_data.update(self.report_data_defect_distribution)
        if self.report_data_resolution_time:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ defect_resolution_time_analysis.html ({len(self.report_data_resolution_time)} keys)")
            template_data.update(self.report_data_resolution_time)
        if self.report_data_recent_defects:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ defect_recent_defects.html ({len(self.report_data_recent_defects)} keys)")
            template_data.update(self.report_data_recent_defects)
        if self.report_data_module_status:
            logger.info(f"ใช้ข้อมูลเฉพาะสำหรับ module_testing_status.html ({len(self.report_data_module_status)} keys)")
            template_data.update(self.report_data_module_status)
        
        # ตรวจสอบและเตรียมข้อมูล TREND_ANALYSIS ที่จำเป็น
        if 'TREND_ANALYSIS' not in template_data:
            logger.warn("⚠️ ไม่พบข้อมูล TREND_ANALYSIS ในรายงาน กำลังใช้ข้อมูลจาก test_data")
            if self.test_data and isinstance(self.test_data, dict) and 'TREND_ANALYSIS' in self.test_data:
                template_data['TREND_ANALYSIS'] = self.test_data['TREND_ANALYSIS']
                logger.info("✅ นำข้อมูล TREND_ANALYSIS จาก test_data มาใช้ได้สำเร็จ")
            else:
                logger.warn("⚠️ ไม่พบข้อมูล TREND_ANALYSIS ใน test_data เช่นกัน")
                # ไม่สร้างข้อมูล hardcode ในที่นี้ แต่ไปสร้างตาม module CORE/test_trend_prepare.py
                logger.info("🔍 กำลังลองเรียก prepare_test_trend_analysis_data อีกครั้งเพื่อดึงข้อมูล TREND_ANALYSIS")
                try:
                    from CORE.test_trend_prepare import prepare_test_trend_analysis_data
                    trend_data = prepare_test_trend_analysis_data(self.test_data or {})
                    if trend_data and 'TREND_ANALYSIS' in trend_data:
                        template_data.update(trend_data)
                        logger.info("✅ เตรียมข้อมูล TREND_ANALYSIS เรียบร้อย")
                    else:
                        logger.warn("⚠️ ยังไม่สามารถสร้างข้อมูล TREND_ANALYSIS ได้")
                except Exception as e:
                    logger.error(f"❌ เกิดข้อผิดพลาดขณะเรียก prepare_test_trend_analysis_data: {str(e)}")
        
        # เพิ่มค่า PROGRESS_STATUS หากยังไม่มี
        if 'PROGRESS_STATUS' not in template_data:
            if 'COMPLETION_PROGRESS' in template_data and 'EXPECTED_PROGRESS' in template_data:
                completion = template_data.get('COMPLETION_PROGRESS', 0)
                expected = template_data.get('EXPECTED_PROGRESS', 0)
                if completion >= expected:
                    template_data['PROGRESS_STATUS'] = 'On Track'
                    template_data['PROGRESS_STATUS_COLOR'] = 'bg-green-100 text-green-800'
                else:
                    template_data['PROGRESS_STATUS'] = 'Behind Schedule'
                    template_data['PROGRESS_STATUS_COLOR'] = 'bg-red-100 text-red-800'
        
        # แสดงข้อมูลสำคัญหลังการอัพเดท
        logger.info(f"🔍 ข้อมูลหลังการอัพเดทก่อนการ render:")
        logger.info(f"  TOTAL_TEST_CASES: {template_data.get('TOTAL_TEST_CASES')}")
        
        # Render HTML
        html_content = self.html_renderer.template_env.get_template(template_file).render(**template_data)
        
        # Save output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"สร้างรายงานเสร็จสมบูรณ์: {output_file}")
        return output_file

    @keyword("Generate QA Report")
    def generate_report(self, output_dir: str = None) -> str:
        """
        ***| Description |***
        - Keyword สำหรับสร้างรายงาน QA HTML จากข้อมูลที่เตรียมไว้
        - ใช้ template และข้อมูลที่ตั้งค่าไว้ใน Setup และเตรียมไว้ด้วย Prepare keywords

        ***| Example |***
        | ${report_path}= | *`Generate QA Report`* | output_dir=path/to/output |

        ***| Parameters |***
        - **`output_dir`** (`str`, optional): Path ไปยัง Directory ที่จะใช้เก็บ Report (ถ้าไม่ระบุจะใช้ค่าที่ตั้งไว้ใน Setup)

        ***| Returns |***
        - **`str`**: Path ไปยังไฟล์รายงานที่สร้างขึ้น

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            # ใช้ output_dir จาก parameter หรือใช้ค่าที่ตั้งไว้ใน Setup
            output_path = os.path.abspath(output_dir) if output_dir else self.output_dir
            
            if not output_path:
                logger.error("ไม่พบ path สำหรับ output directory โปรดระบุผ่าน parameter หรือเรียก Setup QA Report ก่อน")
                return ""
            
            # ตรวจสอบว่ามีข้อมูลสำหรับสร้างรายงานหรือไม่
            if not self.report_data:
                 logger.warning("ไม่มีข้อมูลสำหรับสร้างรายงาน กำลังลองเรียก Prepare Report Data ก่อน")
                 self.prepare_report_data() # ลองเตรียมข้อมูลทั้งหมดอีกครั้ง
                 if not self.report_data:
                     logger.error("ยังคงไม่มีข้อมูลสำหรับสร้างรายงานหลังจากพยายามเตรียมข้อมูลแล้ว")
                     return ""
            
            # ตรวจสอบว่ามี template หรือไม่
            if not self.template_name or not os.path.exists(self.template_name):
                logger.error(f"ไม่พบไฟล์ template: {self.template_name}")
                return ""
            
            # สร้าง output directory ถ้ายังไม่มี
            os.makedirs(output_path, exist_ok=True)
            
            # สร้างรายงานโดยใช้ HTML Renderer
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_path, f"qa_report_{timestamp}.html")
            
            # สร้างรายงานด้วย HTML Renderer
            report_path = self._generate_with_html_renderer(output_file)
            
            logger.info(f"รายงาน QA ถูกสร้างเรียบร้อยแล้วที่: {report_path}")
            return report_path
            
        except Exception as e:
            # เพิ่ม traceback เพื่อดูรายละเอียด error
            import traceback
            logger.error(f"เกิดข้อผิดพลาดในการสร้างรายงาน QA: {str(e)}\n{traceback.format_exc()}")
            return ""

    @keyword("Clear QA Report Cache")
    def clear_qa_report_cache(self) -> None:
        """
        ***| Description |***
        - ล้างข้อมูล cache ทั้งหมดที่เก็บไว้ในระหว่างการทำงานของ QA Report Library
        - เพื่อให้การเริ่มทำงานใหม่ใช้ข้อมูลล่าสุดจากแหล่งข้อมูลต้นทาง

        ***| Example |***
        | *`Clear QA Report Cache`* |

        ***| Returns |***
        - **`None`**

        ***| Create By |***
        | *`Tassana Khrueawan`* |
        """
        try:
            logger = get_logger("QAReportLibrary.Cache")
            
            # รีเซ็ตตัวแปรที่เก็บข้อมูล
            logger.info("⏳ กำลังล้างข้อมูล Cache ทั้งหมด...")
            
            # ล้างข้อมูลรายงานหลัก
            self.report_data = {}
            logger.info("ล้างข้อมูล report_data เรียบร้อยแล้ว")
            
            # ล้างข้อมูลเฉพาะแต่ละส่วน
            self.report_data_test_summary = {}
            self.report_data_defect_trend = {}
            self.report_data_test_trend = {}
            self.report_data_module_status = {}
            self.report_data_defect_distribution = {}
            self.report_data_resolution_time = {}
            self.report_data_recent_defects = {}
            logger.info("ล้างข้อมูลเฉพาะของแต่ละส่วนเรียบร้อยแล้ว")
            
            # ล้างข้อมูลอื่นๆ
            self.test_data = None
            self.defects_data = []
            
            # ล้าง cache ของ UTILS
            clear_cache()
            
            # ล้างตัวแปรอื่นๆ ที่ต้องการรีเซ็ต
            self.data_file = None
            self.defects_file = None
            
            logger.info("Cache ถูกล้างเรียบร้อยแล้ว")
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการล้าง Cache: {str(e)}")
    
    @keyword("Load Test Data")
    def Load_Test_Data(self):
        return self.report_data

    @keyword("Find Key Html Report")
    def find_key_html_report(self, template_path: str = None, filter_keys: bool = False, with_description: bool = True) -> list:
        """
        ค้นหาตัวแปรทั้งหมดที่ใช้ในไฟล์ template HTML
        
        Args:
            template_path (str, optional): เส้นทางไฟล์ template HTML ที่ต้องการค้นหา keys
                                         ถ้าไม่ระบุจะใช้ค่า self.template_name
            filter_keys (bool, optional): กรองเฉพาะตัวแปรที่สำคัญที่มีคำอธิบาย
                                      ถ้าเป็น True จะแสดงเฉพาะตัวแปรที่มีการอธิบายไว้
            with_description (bool, optional): แสดงคำอธิบายของตัวแปรแต่ละตัว
                                        ถ้าเป็น True จะแสดงคำอธิบายของตัวแปรที่มีการอธิบายไว้
        
        Returns:
            list: รายการตัวแปรทั้งหมดที่พบในไฟล์ template
            
        ตัวอย่างการใช้งาน:
            # ค้นหา keys ทั้งหมดในไฟล์ template หลัก
            ${KEYS}=    Find Key Html Report
            
            # ค้นหา keys ทั้งหมดในไฟล์ template อื่น
            ${KEYS}=    Find Key Html Report    path/to/template.html
            
            # ค้นหาและแสดงเฉพาะตัวแปรที่สำคัญพร้อมคำอธิบาย
            ${KEYS}=    Find Key Html Report    path/to/template.html    filter_keys=${TRUE}
        """
        # ใช้ template_path ที่ส่งมา หรือ template_name ที่ตั้งค่าไว้
        template_path = template_path or self.template_name
        
        # สร้าง TemplateFinder และใช้วิธีการค้นหาแบบใหม่
        finder = TemplateFinder()
        return finder.find_template_keys(template_path, filter_keys, with_description)

    @keyword("Check Template Key Exists")
    def check_template_key_exists(self, template_path: str, key_name: str) -> bool:
        """
        ตรวจสอบว่ามีตัวแปร (key) ชื่อที่ระบุอยู่ในไฟล์ template หรือไม่
        
        Args:
            template_path (str): เส้นทางไฟล์ template HTML ที่ต้องการตรวจสอบ
            key_name (str): ชื่อตัวแปรที่ต้องการตรวจสอบ
        
        Returns:
            bool: True หากพบตัวแปรในไฟล์ template, False หากไม่พบ
            
        ตัวอย่างการใช้งาน:
            ${EXISTS}=    Check Template Key Exists    path/to/template.html    PROJECT_NAME
        """
        # สร้าง TemplateFinder และใช้วิธีการตรวจสอบแบบใหม่
        finder = TemplateFinder()
        return finder.check_key_exists(template_path, key_name)

    @keyword("Get Template Keys With Value")
    def get_template_keys_with_value(self, template_path: str = None, key_filter: str = None) -> dict:
        """
        ดึงข้อมูลตัวแปรในไฟล์ template พร้อมค่าที่จะใช้ในการ render
        
        Args:
            template_path (str, optional): เส้นทางไฟล์ template HTML ที่ต้องการตรวจสอบ
                                           ถ้าไม่ระบุจะใช้ค่า self.template_name
            key_filter (str, optional): กรองเฉพาะตัวแปรที่ชื่อตรงกับคำที่ระบุ
                                        ถ้าไม่ระบุจะแสดงทั้งหมด
        
        Returns:
            dict: Dictionary ที่มี key เป็นชื่อตัวแปร และ value เป็นค่าที่จะใช้ render
            
        ตัวอย่างการใช้งาน:
            # ดูค่าตัวแปรทั้งหมดในไฟล์ template
            ${KEY_VALUES}=    Get Template Keys With Value    path/to/template.html
            
            # ดูเฉพาะตัวแปรที่มีคำว่า "PROJECT" ในชื่อ
            ${PROJECT_KEY_VALUES}=    Get Template Keys With Value    path/to/template.html    PROJECT
        """
        logger = get_logger("QAReportLibrary.KeyValueFinder")
        
        # ใช้ template_path ที่ส่งมา หรือ template_name ที่ตั้งค่าไว้
        template_path = template_path or self.template_name
        
        if not template_path:
            logger.error("ไม่ได้ระบุ template_path และไม่มีการตั้งค่า template_name")
            return {}
        
        if not os.path.exists(template_path):
            logger.error(f"ไม่พบไฟล์ template: {template_path}")
            return {}
        
        # ตรวจสอบว่ามีข้อมูลสำหรับ render หรือไม่
        if not self.report_data:
            logger.warning("⚠️ ไม่มีข้อมูลสำหรับ render รายงาน กำลังเตรียมข้อมูลเริ่มต้น...")
            self.prepare_report_data()
            
            if not self.report_data:
                logger.error("ไม่สามารถเตรียมข้อมูลสำหรับ render รายงานได้")
                return {}
        
        # หา keys ทั้งหมดในไฟล์ template
        all_keys = self.find_key_html_report(template_path)
        
        # กรองตามคำค้นหา (ถ้ามี)
        if key_filter:
            filtered_keys = [key for key in all_keys if key_filter.lower() in key.lower()]
        else:
            filtered_keys = all_keys
        
        # เตรียมข้อมูลสำหรับส่งคืน
        key_values = {}
        
        # ตรวจสอบว่าแต่ละ key มีค่าในข้อมูลที่จะใช้ render หรือไม่
        for key in filtered_keys:
            # ตรวจสอบตัวแปรแบบ nested (เช่น data.value)
            parts = key.split('.')
            if len(parts) > 1:
                # ตรวจสอบตัวแปรแบบ nested
                curr = self.report_data
                found = True
                for part in parts:
                    if isinstance(curr, dict) and part in curr:
                        curr = curr[part]
                    else:
                        found = False
                        break
                
                if found:
                    key_values[key] = curr
                else:
                    key_values[key] = None
            else:
                # ตรวจสอบตัวแปรปกติ
                if key in self.report_data:
                    key_values[key] = self.report_data[key]
                else:
                    key_values[key] = None
        
        # แสดงผลลัพธ์
        logger.info(f"🔍 พบตัวแปรที่ตรงกับเงื่อนไข {len(key_values)} keys")
        logger.info(f"====================== TEMPLATE KEY VALUES ======================")
        
        # จัดกลุ่มตามค่า (มีค่า/ไม่มีค่า)
        has_value_keys = {}
        no_value_keys = {}
        
        for key, value in key_values.items():
            if value is not None:
                has_value_keys[key] = value
            else:
                no_value_keys[key] = None
        
        # แสดงตัวแปรที่มีค่า
        logger.info(f"\n🔹 ตัวแปรที่มีค่า ({len(has_value_keys)} keys):")
        for idx, (key, value) in enumerate(sorted(has_value_keys.items()), 1):
            # ปรับรูปแบบการแสดงผลตามประเภทข้อมูล
            if isinstance(value, dict):
                value_str = f"dict ({len(value)} keys)"
            elif isinstance(value, list):
                value_str = f"list ({len(value)} items)"
            elif isinstance(value, str) and len(value) > 100:
                value_str = f"'{value[:100]}...' ({len(value)} ตัวอักษร)"
            else:
                value_str = str(value)
            
            logger.info(f"  {idx}. {key} = {value_str}")
        
        # แสดงตัวแปรที่ไม่มีค่า
        if no_value_keys:
            logger.info(f"\n🔹 ตัวแปรที่ไม่มีค่า ({len(no_value_keys)} keys):")
            for idx, key in enumerate(sorted(no_value_keys.keys()), 1):
                logger.info(f"  {idx}. {key} = None")
        
        logger.info(f"=============================================================")
        
        return key_values

