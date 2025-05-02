# QAReportLibrary2/UTILS/utils.py
import pytz
from datetime import datetime, timedelta
import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
import functools
import time
import json
from robot.api import logger 
import logging.handlers


THAI_TIMEZONE = "Asia/Bangkok"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_ENABLE_CACHING = True
DEFAULT_CACHE_DURATION = 300

# เพิ่มตัวแปรเพื่อติดตามว่าได้ตั้งค่า logging ไปแล้วหรือยัง
_logging_initialized = False
_log_handlers = {}
_loggers = {}


def setup_logging(log_level: str = DEFAULT_LOG_LEVEL, log_format: str = DEFAULT_LOG_FORMAT, log_to_file: bool = False, log_file_path: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: The log message format
        log_to_file: Whether to log to a file
        log_file_path: Path to log file, if not provided will use default in LOG directory
    
    Returns:
        Logger: The configured logger
    """
    global _logging_initialized, _log_handlers
    
    # แปลงระดับ log เป็นค่าที่ถูกต้อง
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO)
    
    # ตั้งค่า root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # สร้าง handler สำหรับแสดงผลใน console ถ้ายังไม่มี
    if 'console' not in _log_handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        _log_handlers['console'] = console_handler
    
    # ถ้าต้องการ log ไปยังไฟล์และยังไม่มี file handler
    if log_to_file:
        # กำหนด path ของไฟล์ log
        if not log_file_path:
            # สร้าง path ไปยังโฟลเดอร์ LOG ใน project root
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(current_dir, "LOG")
            os.makedirs(log_dir, exist_ok=True)
            
            # สร้างชื่อไฟล์ log ตามวันที่
            today = datetime.now().strftime("%Y-%m-%d")
            log_file_path = os.path.join(log_dir, f"qa_report_{today}.log")
        
        # ถ้ายังไม่มี file handler สำหรับไฟล์นี้
        file_handler_key = f'file:{log_file_path}'
        if file_handler_key not in _log_handlers:
            # สร้าง rotating file handler (หมุนเวียนไฟล์เมื่อขนาดเกิน 5MB)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            _log_handlers[file_handler_key] = file_handler
            
            # Log เพียงครั้งเดียวเมื่อตั้งค่า file handler ใหม่
            if not _logging_initialized:
                root_logger.info(f"Logging to file: {log_file_path}")
                _logging_initialized = True
    
    return root_logger

# ตั้งค่า log เริ่มต้น
log = setup_logging()


def get_logger(name: str = None) -> logging.Logger:
    """
    ฟังก์ชันสำหรับรับ logger ที่มีการตั้งค่าแล้ว
    
    Args:
        name: ชื่อของ logger
    
    Returns:
        Logger: Logger ที่ตั้งค่าแล้ว
    """
    global _loggers
    
    if name is None:
        name = "QAReportLibrary"
    
    # ถ้าเคยสร้าง logger นี้แล้ว ให้ใช้อันเดิม
    if name in _loggers:
        return _loggers[name]
    
    # กำหนดให้เขียน log ลงไฟล์โดยอัตโนมัติ
    log_to_file = True
    
    # สร้าง logger
    logger = logging.getLogger(name)
    
    # ถ้า logger ยังไม่มี handler (ยังไม่ได้ตั้งค่า) และยังไม่มีการตั้งค่า logging
    if not _logging_initialized:
        # ตั้งค่า logger ด้วย setup_logging เพียงครั้งเดียว
        setup_logging(log_to_file=log_to_file)
    
    # เพิ่มฟังก์ชัน error ที่ปลอดภัยขึ้น
    def safe_error(msg, *args, **kwargs):
        """
        ฟังก์ชัน error ที่ไม่พยายามเรียกใช้ args อย่างอัตโนมัติซึ่งอาจทำให้เกิด error ซ้อน error
        """
        if args:
            try:
                msg = msg % args
            except Exception:
                msg = f"{msg} (error formatting message with args: {args})"
        logger.error(msg)
    
    # แทนที่ฟังก์ชัน error ด้วย safe_error
    logger.original_error = logger.error
    logger.error = safe_error
    
    # เก็บ logger นี้ไว้ใช้ซ้ำ
    _loggers[name] = logger
    
    return logger


_cache: Dict[str, Tuple[Any, float]] = {}
_cache_times: Dict[str, float] = {}

def cache(duration: int = DEFAULT_CACHE_DURATION):
    """
    Caching decorator for functions
    
    Args:
        duration (int): Cache duration in seconds
    
    Returns:
        Callable: Decorated function with caching
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            now = time.time()
            
            # Check if cached result exists and is valid
            if key in _cache and (now - _cache_times.get(key, 0)) < duration:
                return _cache[key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_times[key] = now
            
            return result
        return wrapper
    return decorator

def clear_cache() -> None:
    """
    Clear all cached data.
    """
    global _cache
    _cache = {}
    _cache_times = {}
    log.info("Cache cleared")


def format_datetime_thai(dt: Union[str, datetime], include_time: bool = False) -> str:
    """
    แปลงวันที่เวลาให้อยู่ในรูปแบบไทย
    
    Args:
        dt (Union[str, datetime]): วันที่ในรูปแบบ string หรือ datetime object
        include_time (bool): รวมเวลาด้วยหรือไม่
        
    Returns:
        str: วันที่ในรูปแบบไทย เช่น "15 มกราคม 2566" หรือ "15 มกราคม 2566 14:30:00"
    """
    if not dt:
        return ""
    
    # ถ้าเป็น string ให้แปลงเป็น datetime
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
            else:
                dt = datetime.strptime(dt, '%Y-%m-%d')
        except ValueError:
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return dt  # ถ้าแปลงไม่ได้ให้คืนค่าเดิม
    
    # ตรวจสอบว่าเป็น datetime object
    if not isinstance(dt, datetime):
        return str(dt)
    
    # กำหนด timezone เป็นไทย
    thai_timezone = pytz.timezone(THAI_TIMEZONE)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    dt = dt.astimezone(thai_timezone)
    
    # ชื่อเดือนภาษาไทย
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    # สร้างวันที่แบบไทย
    thai_date = f"{dt.day} {thai_months[dt.month-1]} {dt.year + 543}"
    
    # เพิ่มเวลาถ้าต้องการ
    if include_time:
        thai_date += f" {dt.strftime('%H:%M:%S')}"
    
    return thai_date

def calculate_sprint_days(start_date_str: str, end_date_str: str, now: Optional[datetime] = None) -> Tuple[int, int, int, float]:
    """
    คำนวณข้อมูลวันที่ของ Sprint
    
    Args:
        start_date_str (str): วันเริ่มต้น Sprint ในรูปแบบ "YYYY-MM-DD"
        end_date_str (str): วันสิ้นสุด Sprint ในรูปแบบ "YYYY-MM-DD"
        now (Optional[datetime]): วันที่ปัจจุบัน (ถ้าไม่ระบุจะใช้วันที่ปัจจุบัน)
        
    Returns:
        Tuple[int, int, int, float]: 
            - total_days: จำนวนวันทั้งหมดใน Sprint
            - days_passed: จำนวนวันที่ผ่านไปแล้ว
            - days_remaining: จำนวนวันที่เหลือ
            - progress_per_day: อัตราความก้าวหน้าต่อวัน (%)
    """
    if not start_date_str or not end_date_str:
        return 0, 0, 0, 0.0
    
    try:
        # แปลง string เป็น datetime
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        # ใช้เวลาปัจจุบันหรือเวลาที่กำหนด
        current_date = now if now else datetime.now()
        
        # คำนวณจำนวนวันทั้งหมด
        total_days = (end_date - start_date).days + 1  # รวมวันเริ่มต้นและสิ้นสุด
        
        # คำนวณจำนวนวันที่ผ่านไป
        days_passed = (current_date.date() - start_date.date()).days + 1
        days_passed = max(0, min(days_passed, total_days))  # ให้อยู่ในช่วงที่ถูกต้อง
        
        # คำนวณจำนวนวันที่เหลือ
        days_remaining = total_days - days_passed
        days_remaining = max(0, days_remaining)  # ให้ไม่ติดลบ
        
        # คำนวณอัตราความก้าวหน้าต่อวัน
        progress_per_day = 100.0 / total_days if total_days > 0 else 0
        
        return total_days, days_passed, days_remaining, progress_per_day
        
    except ValueError as e:
        log.warning(f"Error in calculate_sprint_days: {e}")
        return 0, 0, 0, 0.0


class TemplateUtils:
    @staticmethod
    def to_datetime(date_str: str) -> Optional[datetime]:
        if not isinstance(date_str, str):
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            log.warning(f"Could not parse date string: {date_str}")
            return None
    
    @staticmethod
    def format_datetime(dt: Union[str, datetime], include_time: bool = True) -> str:
        """แปลงวันที่เวลาให้อยู่ในรูปแบบที่เหมาะสม"""
        return format_datetime_thai(dt, include_time)
    
    @staticmethod
    def format_date(dt: Union[str, datetime]) -> str:
        """แปลงวันที่ให้อยู่ในรูปแบบวันที่เท่านั้น"""
        return format_datetime_thai(dt, include_time=False)
    
    @staticmethod
    def as_percent(value: Union[int, float, None], precision: int = 1) -> str:
        """แปลงค่าเป็นรูปแบบเปอร์เซ็นต์"""
        if value is None:
            return "0%"
        try:
            return f"{float(value):.{precision}f}%"
        except (ValueError, TypeError):
            return "0%"
    
    @staticmethod
    def format_number(value: Union[int, float, None], precision: int = 1) -> str:
        if value is None:
            return ""
        try:
            if isinstance(value, int):
                return f"{value:,}"
            elif isinstance(value, float):
                 return f"{value:,.{precision}f}"
            else:
                 return f"{float(value):,.{precision}f}"
        except (ValueError, TypeError):
             log.warning(f"Could not format number: {value}")
             return str(value)
    
    @staticmethod
    def safe_json_loads(json_str: Optional[str], default: Any = None) -> Any:
        if not json_str:
            return default or {}
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            log.warning(f"Could not parse JSON string: {json_str[:50]}... Error: {e}")
            return default or {}
    
    @staticmethod
    def ensure_dict(value: Any) -> Dict[str, Any]:
        """
        ตรวจสอบให้แน่ใจว่าค่าที่รับเข้ามาเป็น dictionary
        ถ้าเป็น string ที่มีรูปแบบ JSON จะแปลงเป็น dictionary
        ถ้าไม่ใช่ dictionary จะส่งคืน empty dictionary
        
        Args:
            value (Any): ค่าที่ต้องการตรวจสอบ
            
        Returns:
            Dict[str, Any]: dictionary ที่ได้จากการแปลง หรือ empty dictionary
        """
        if isinstance(value, dict):
            return value
            
        if isinstance(value, str):
            try:
                result = json.loads(value)
                if isinstance(result, dict):
                    return result
            except (json.JSONDecodeError, ValueError):
                pass
                
        return {}
    
    @staticmethod
    def default_dict(value: Any, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ส่งคืน dictionary ที่กำหนดถ้า value ไม่ใช่ dictionary
        
        Args:
            value (Any): ค่าที่ต้องการตรวจสอบ
            default (Dict[str, Any], optional): ค่าเริ่มต้นถ้า value ไม่ใช่ dictionary
            
        Returns:
            Dict[str, Any]: value หรือ default
        """
        if isinstance(value, dict):
            return value
            
        if default is None:
            default = {}
            
        return default

