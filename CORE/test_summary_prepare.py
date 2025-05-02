"""
Test Summary Prepare Module
รับผิดชอบการเตรียมข้อมูลสรุปผลการทดสอบ

Author: Tassana Khrueawan
Version: 2.1.0
"""

from robot.api import logger
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, Any, Optional, List

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from UTILS import get_logger, format_datetime_thai, calculate_sprint_days
from CORE.metrics_calculator import calculate_test_metrics

# Setup logger
logger = get_logger("TestSummaryPrepare")

def prepare_test_summary_data(test_data: Dict[str, Any] = None, data_file: str = None) -> Dict[str, Any]:
    try:
        if not test_data and data_file:
            if not os.path.exists(data_file):
                logger.error(f"ไม่พบไฟล์ test data: {data_file}")
                return {}
                
            try:
                import json
                with open(data_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                logger.info(f"โหลดข้อมูล test data จาก: {data_file}")
            except Exception as e:
                logger.error(f"ไม่สามารถโหลดข้อมูล test data: {str(e)}")
                return {}
        
        if not test_data:
            logger.error("ไม่มีข้อมูล test data สำหรับการเตรียม Test Summary")
            return {}
        
        # 2. เตรียมข้อมูล Test Summary
        logger.info("⏳ กำลังเตรียมข้อมูล Test Summary...")
        
        # คำนวณเมตริกจากข้อมูล test
        test_metrics = calculate_test_metrics(test_data)
        
        # ดึงข้อมูลจาก test_data (สำหรับกรณีที่มีโครงสร้าง testCases)
        test_cases = test_data.get('testCases', {})
        total_tc = int(test_cases.get('TOTAL', test_metrics.get('total_tests', 0)))
        passed_tc = int(test_cases.get('PASS', test_metrics.get('total_tests', 0) * test_metrics.get('pass_rate', 0) / 100))
        failed_tc = int(test_cases.get('FAIL', test_metrics.get('total_tests', 0) * test_metrics.get('fail_rate', 0) / 100))
        blocked_tc = int(test_cases.get('BLOCK', 0))
        in_progress_tc = int(test_cases.get('IN_PROGRESS', 0))
        not_started_tc = int(test_cases.get('NOT_STARTED', 0))
        
        # ข้อมูล sprint และ timeline
        dashboard = test_data.get('dashboard', {})
        start_date = dashboard.get('START_DATE', '2023-01-01') 
        end_date = dashboard.get('END_DATE', '2023-12-31')
        
        # คำนวณวันที่ของ Sprint
        total_days, days_passed, days_remaining, progress_per_day = calculate_sprint_days(
            start_date, end_date
        )
        
        # คำนวณความคืบหน้า
        completion_progress = round((passed_tc / total_tc) * 100, 1) if total_tc > 0 else 0.0
        remaining_progress = round(100 - completion_progress, 1)
        
        # ประเมินความเสี่ยง
        actual_progress_rate = (completion_progress / days_passed) if days_passed > 0 else 0
        expected_progress = (100 / total_days) * days_passed if total_days > 0 else 0
        days_to_completion = (remaining_progress / actual_progress_rate) if actual_progress_rate > 0 else 999
        days_difference = days_to_completion - days_remaining
        
        # ระดับความเสี่ยง
        risk_level, risk_level_th, risk_level_color = determine_risk_level(days_difference)
        
        # สร้างข้อมูลสำหรับส่วน Test Summary (flat key-value)
        test_summary_data = {
            # ข้อมูลพื้นฐาน Test Cases
            'TOTAL_TEST_CASES': total_tc,                 # จำนวน Test Cases ทั้งหมด (จาก testCases['TOTAL'] หรือรวม test cases ทั้งหมด)
            'PASSED_TEST_CASES': passed_tc,               # จำนวนที่ผ่าน (จาก testCases['PASS'] หรือคำนวณจาก pass_rate)
            'FAILED_TEST_CASES': failed_tc,               # จำนวนที่ไม่ผ่าน (จาก testCases['FAIL'] หรือคำนวณจาก fail_rate)
            'BLOCKED_TEST_CASES': blocked_tc,             # จำนวนที่ Blocked (จาก testCases['BLOCK'])
            'IN_PROGRESS_TEST_CASES': in_progress_tc,     # จำนวนที่อยู่ระหว่างดำเนินการ (จาก testCases['IN_PROGRESS'])
            'NOT_STARTED_TEST_CASES': not_started_tc,     # จำนวนที่ยังไม่เริ่ม (จาก testCases['NOT_STARTED'])
            
            # ข้อมูลความคืบหน้า
            'COMPLETION_PROGRESS': completion_progress,   # % ความคืบหน้า: (PASSED_TEST_CASES / TOTAL_TEST_CASES) * 100
            'REMAINING_PROGRESS': remaining_progress,     # % ที่เหลือต้องทำ: 100 - COMPLETION_PROGRESS
            'PASS_RATE': test_metrics.get('pass_rate', 0),    # อัตราผ่าน (%) (จากฟังก์ชัน calculate_test_metrics)
            'FAIL_RATE': test_metrics.get('fail_rate', 0),    # อัตราไม่ผ่าน (%) (จากฟังก์ชัน calculate_test_metrics)
            'SKIP_RATE': test_metrics.get('skip_rate', 0),    # อัตราถูกข้าม (%) (จากฟังก์ชัน calculate_test_metrics)
            
            # ข้อมูล Timeline (Sprint)
            'START_DATE': start_date,                     # วันที่เริ่ม Sprint (จาก dashboard หรือ default)
            'END_DATE': end_date,                         # วันที่สิ้นสุด Sprint (จาก dashboard หรือ default)
            'TOTAL_DAYS': total_days,                     # รวมจำนวนวันใน Sprint (END_DATE - START_DATE + 1)
            'DAYS_PASSED': days_passed,                   # จำนวนวันที่ผ่านไป (current_date - START_DATE + 1)
            'DAYS_REMAINING': days_remaining,             # จำนวนวันที่เหลือใน Sprint (TOTAL_DAYS - DAYS_PASSED)
            'PROGRESS_PER_DAY': progress_per_day,         # อัตราความก้าวหน้าต่อวัน (%| 100/TOTAL_DAYS)
            'DAYS_TO_COMPLETION': int(days_to_completion),# ประมาณวันที่จะเสร็จสมบูรณ์ (REMAINING_PROGRESS/ACTUAL_PROGRESS_RATE)
            'DAYS_DIFFERENCE': int(days_difference),      # ต่างจากวันที่เหลือจริงเท่าไหร่ (DAYS_TO_COMPLETION - DAYS_REMAINING)
            
            # ข้อมูลความเสี่ยง (Risk)
            'RISK_LEVEL': risk_level,                     # รหัสความเสี่ยง (NONE/LOW/MEDIUM/HIGH/CRITICAL) (คำนวณจาก DAYS_DIFFERENCE)
            'RISK_LEVEL_TH': risk_level_th,               # ระดับความเสี่ยง ภาษาไทย
            'RISK_LEVEL_COLOR': risk_level_color,         # สีความเสี่ยง (class สีสำหรับแสดงผล)
            'EXPECTED_PROGRESS': expected_progress,       # % ความคืบหน้าที่ควรจะถึง ณ ปัจจุบัน (คำนวณจาก days ผ่านไป)
            'ACTUAL_PROGRESS': test_metrics.get('actual_progress', 0), # % ความคืบหน้าจริง (pass_rate)
            'ACTUAL_PROGRESS_RATE': round(actual_progress_rate, 2)     # % ความคืบหน้าจริงต่อวัน (COMPLETION_PROGRESS / DAYS_PASSED)
        }
        
        # Log ข้อมูลสำคัญที่ได้
        logger.info("✅ สรุป Test Summary Data:")
        for k, v in test_summary_data.items():
            logger.info(f"  {k}: {v}")
        
        return test_summary_data
        
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการเตรียม Test Summary Data: {str(e)}")
        return {}

def determine_risk_level(days_difference: int) -> tuple:
    """
    กำหนดระดับความเสี่ยงจากจำนวนวันที่แตกต่าง
    
    Args:
        days_difference (int): จำนวนวันที่แตกต่างระหว่างวันที่คาดการณ์กับวันที่เหลือจริง
        
    Returns:
        tuple: (risk_level, risk_level_th, risk_level_color) - รหัสความเสี่ยง, ข้อความภาษาไทย, รหัสสี
    """
    if days_difference <= 0:
        return "NONE", "ไม่มีความเสี่ยง", "text-green-500"
    elif days_difference <= 5:
        return "LOW", "ความเสี่ยงต่ำ", "text-amber-500"
    elif days_difference <= 10:
        return "MEDIUM", "ความเสี่ยงปานกลาง", "text-orange-500"
    elif days_difference <= 20:
        return "HIGH", "ความเสี่ยงสูง", "text-red-500"
    else:
        return "CRITICAL", "ความเสี่ยงวิกฤต", "text-rose-500"

def generate_risk_recommendation(risk_level: str, days_difference: int, actual_progress_rate: float) -> Dict[str, str]:
    """
    สร้างคำแนะนำตามระดับความเสี่ยง
    
    Args:
        risk_level (str): ระดับความเสี่ยง
        days_difference (int): จำนวนวันที่แตกต่าง
        actual_progress_rate (float): อัตราความก้าวหน้าที่เกิดขึ้นจริง
        
    Returns:
        Dict[str, str]: คำแนะนำในรูปแบบภาษาไทยและอังกฤษ
    """
    if risk_level == "NONE":
        return {
            "th": "ไม่มีความเสี่ยง โปรเจคมีความคืบหน้าเป็นไปตามแผน",
            "en": "No risk, project is on track"
        }
    elif risk_level == "LOW":
        return {
            "th": f"มีความเสี่ยงต่ำ โปรเจคอาจล่าช้า {days_difference} วัน ควรพิจารณาเพิ่มความเร็วการทำงานเล็กน้อย",
            "en": f"Low risk, project may be delayed by {days_difference} days. Consider slightly increasing work velocity"
        }
    elif risk_level == "MEDIUM":
        return {
            "th": f"มีความเสี่ยงปานกลาง โปรเจคอาจล่าช้า {days_difference} วัน ควรพิจารณาเพิ่มทรัพยากรหรือปรับกระบวนการทำงาน",
            "en": f"Medium risk, project may be delayed by {days_difference} days. Consider adding resources or optimizing workflow"
        }
    elif risk_level == "HIGH":
        return {
            "th": f"มีความเสี่ยงสูง โปรเจคอาจล่าช้า {days_difference} วัน ควรเพิ่มทรัพยากรและปรับกระบวนการทำงานโดยเร่งด่วน",
            "en": f"High risk, project may be delayed by {days_difference} days. Urgent action needed: add resources and optimize workflow"
        }
    else:  # CRITICAL
        return {
            "th": f"มีความเสี่ยงวิกฤต โปรเจคอาจล่าช้า {days_difference} วัน ควรพิจารณาปรับขอบเขตงานหรือเลื่อนกำหนดส่งมอบ",
            "en": f"Critical risk, project may be delayed by {days_difference} days. Consider reducing scope or extending deadline"
        } 
