# CORE/metrics_calculator.py

"""
Metrics Calculator Module
โมดูลสำหรับคำนวณเมตริกต่างๆ สำหรับการสร้างรายงาน QA

Author: Tassana Khrueawan
Version: 2.0.0
"""

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger

logger = get_logger("MetricsCalculator")

def calculate_test_metrics(test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    คำนวณเมตริกต่างๆ เกี่ยวกับการทดสอบ

    Args:
        test_data (List[Dict[str, Any]]): ข้อมูลการทดสอบทั้งหมด

    Returns:
        Dict[str, Any]: เมตริกต่างๆ เกี่ยวกับการทดสอบ
    """
    if not test_data:
        logger.error("ไม่มีข้อมูลการทดสอบให้คำนวณ")
        return {
            'total_tests': 0,
            'pass_rate': 0,
            'fail_rate': 0,
            'skip_rate': 0,
            'expected_progress': 0,
            'actual_progress': 0,
            'risk_level': 'HIGH',
            'test_coverage': 0
        }
    
    # เช็คว่า test_data เป็น str หรือไม่
    if isinstance(test_data, str):
        logger.error(f"ข้อมูล test_data เป็น string ไม่สามารถคำนวณได้: {test_data[:50]}...")
        return {
            'total_tests': 0,
            'pass_rate': 0,
            'fail_rate': 0,
            'skip_rate': 0,
            'expected_progress': 0,
            'actual_progress': 0,
            'risk_level': 'HIGH',
            'test_coverage': 0
        }
    
    # เช็คว่า test_data เป็น dict หรือไม่ (กรณีที่ไม่ใช่ list)
    if isinstance(test_data, dict):
        # ถ้ามี key 'testCases' ให้ใช้ข้อมูลจาก testCases
        if 'testCases' in test_data:
            test_cases = test_data['testCases']
            
            # ถ้า test_cases เป็น dict และมีค่า TOTAL, PASS, FAIL
            if isinstance(test_cases, dict):
                total_tests = int(test_cases.get('TOTAL', 0))
                passes = int(test_cases.get('PASS', 0))
                fails = int(test_cases.get('FAIL', 0))
                skips = int(test_cases.get('SKIP', test_cases.get('SKIPPED', 0)))
                
                # คำนวณอัตราส่วน
                pass_rate = round((passes / total_tests) * 100, 2) if total_tests > 0 else 0
                fail_rate = round((fails / total_tests) * 100, 2) if total_tests > 0 else 0
                skip_rate = round((skips / total_tests) * 100, 2) if total_tests > 0 else 0
                
                # คำนวณความคืบหน้าที่คาดหวัง
                expected_progress = _calculate_expected_progress()
                
                # คำนวณความคืบหน้าจริง
                actual_progress = pass_rate
                
                # ประเมินระดับความเสี่ยง
                risk_level = _evaluate_test_risk(expected_progress, actual_progress, fail_rate)
                
                # สร้างผลลัพธ์
                return {
                    'total_tests': total_tests,
                    'pass_rate': pass_rate,
                    'fail_rate': fail_rate,
                    'skip_rate': skip_rate,
                    'expected_progress': expected_progress,
                    'actual_progress': actual_progress,
                    'risk_level': risk_level,
                    'test_coverage': 0
                }
        
        # กรณีที่ไม่มี key 'testCases' ให้ใช้ข้อมูลทั้งหมด (ถ้าทำได้)
        logger.warning("ข้อมูล test_data เป็น dictionary แต่ไม่มี key 'testCases' ที่ใช้งานได้")
        return {
            'total_tests': 0,
            'pass_rate': 0,
            'fail_rate': 0,
            'skip_rate': 0,
            'expected_progress': 0,
            'actual_progress': 0,
            'risk_level': 'HIGH',
            'test_coverage': 0
        }

    try:
        # นับจำนวนเทสเคสทั้งหมด
        total_tests = len(test_data)
        
        # นับตามสถานะ
        passes = sum(1 for t in test_data if t.get('status', '').lower() == 'pass')
        fails = sum(1 for t in test_data if t.get('status', '').lower() == 'fail')
        skips = sum(1 for t in test_data if t.get('status', '').lower() in ['skip', 'skipped'])
        
        # คำนวณอัตราส่วน
        pass_rate = round((passes / total_tests) * 100, 2) if total_tests > 0 else 0
        fail_rate = round((fails / total_tests) * 100, 2) if total_tests > 0 else 0
        skip_rate = round((skips / total_tests) * 100, 2) if total_tests > 0 else 0
        
        # คำนวณความคืบหน้าที่คาดหวัง (ตามตาราง timeline)
        expected_progress = _calculate_expected_progress()
        
        # คำนวณความคืบหน้าจริง (จาก pass rate)
        actual_progress = pass_rate
        
        # ประเมินระดับความเสี่ยง
        risk_level = _evaluate_test_risk(expected_progress, actual_progress, fail_rate)
        
        # คำนวณค่า test coverage โดยประมาณ (ถ้ามีข้อมูล)
        test_coverage = _calculate_test_coverage(test_data)
        
        # คำนวณเมตริกตาม module
        module_metrics = _calculate_module_metrics(test_data)
        
        return {
            'total_tests': total_tests,
            'pass_rate': pass_rate,
            'fail_rate': fail_rate,
            'skip_rate': skip_rate,
            'expected_progress': expected_progress,
            'actual_progress': actual_progress,
            'risk_level': risk_level,
            'test_coverage': test_coverage,
            'module_metrics': module_metrics
        }
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการคำนวณเมตริกการทดสอบ: {str(e)}")
        return {
            'error': f"เกิดข้อผิดพลาดในการคำนวณ: {str(e)}",
            'total_tests': 0,
            'pass_rate': 0,
            'fail_rate': 0,
            'skip_rate': 0,
            'expected_progress': 0,
            'actual_progress': 0,
            'risk_level': 'HIGH',
            'test_coverage': 0
        }

def calculate_defect_metrics(defect_data: List[Dict[str, Any]], total_tests: int = 0) -> Dict[str, Any]:
    """
    คำนวณเมตริกต่างๆ เกี่ยวกับข้อบกพร่อง (defects)

    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        total_tests (int): จำนวนข้อทดสอบทั้งหมด

    Returns:
        Dict[str, Any]: เมตริกต่างๆ เกี่ยวกับข้อบกพร่อง
    """
    if not defect_data:
        logger.error("ไม่มีข้อมูลข้อบกพร่องให้คำนวณ")
        return {
            'total_defects': 0,
            'open_defects': 0,
            'closed_defects': 0,
            'defect_density': 0,
            'severity_distribution': {},
            'status_distribution': {},
            'defect_trends': [],
            'avg_resolution_time': 0,
            'defect_arrival_rate': 0,
            'defect_close_rate': 0
        }

    try:
        # นับจำนวนข้อบกพร่องทั้งหมด
        total_defects = len(defect_data)
        
        # สถานะที่ถือว่าเปิดอยู่และปิดแล้ว
        open_statuses = ['open', 'in progress', 'reopened', 'new']
        closed_statuses = ['closed', 'fixed', 'resolved', 'completed', 'done']
        
        # นับตามสถานะ
        open_defects = sum(1 for d in defect_data if d.get('status', '').lower() in open_statuses)
        closed_defects = sum(1 for d in defect_data if d.get('status', '').lower() in closed_statuses)
        
        # คำนวณ defect density
        defect_density = _calculate_defect_density(total_defects)
        
        # การกระจายตามความรุนแรง
        severity_distribution = _analyze_severity_distribution(defect_data)
        
        # การกระจายตามสถานะ
        status_distribution = _analyze_status_distribution(defect_data)
        
        # แนวโน้มข้อบกพร่อง
        defect_trends = _calculate_defect_trends(defect_data)
        
        # เวลาเฉลี่ยในการแก้ไข
        avg_resolution_time = _calculate_avg_resolution_time(defect_data)
        
        # อัตราการเข้ามาของข้อบกพร่อง
        defect_arrival_rate = _calculate_defect_arrival_rate(defect_data)
        
        # อัตราการปิดข้อบกพร่อง
        defect_close_rate = _calculate_defect_close_rate(defect_data)
        
        return {
            'total_defects': total_defects,
            'open_defects': open_defects,
            'closed_defects': closed_defects,
            'defect_density': defect_density,
            'severity_distribution': severity_distribution,
            'status_distribution': status_distribution,
            'defect_trends': defect_trends,
            'avg_resolution_time': avg_resolution_time,
            'defect_arrival_rate': defect_arrival_rate,
            'defect_close_rate': defect_close_rate
        }
    
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการคำนวณเมตริกข้อบกพร่อง: {str(e)}")
        return {
            'error': f"เกิดข้อผิดพลาดในการคำนวณ: {str(e)}",
            'total_defects': 0,
            'open_defects': 0,
            'closed_defects': 0,
            'defect_density': 0,
            'severity_distribution': {},
            'status_distribution': {},
            'defect_trends': [],
            'avg_resolution_time': 0,
            'defect_arrival_rate': 0,
            'defect_close_rate': 0
        }

def _calculate_expected_progress() -> float:
    """
    คำนวณความคืบหน้าที่คาดหวังโดยอิงจากวันปัจจุบันเทียบกับ timeline ของโปรเจค
    
    Returns:
        float: เปอร์เซ็นต์ความคืบหน้าที่ควรจะเป็น
    """
    # กำหนดวันเริ่มต้นและวันสิ้นสุดของโปรเจค (ตัวอย่าง)
    now = datetime.now()
    
    # ตัวอย่าง: สมมติว่าโปรเจคเริ่ม 1 มกราคม 2023 และสิ้นสุด 31 ธันวาคม 2023
    # ในโค้ดจริงควรดึงค่าจาก configuration หรือ input parameter
    project_start = datetime(now.year, 1, 1)
    project_end = datetime(now.year, 12, 31)
    
    # คำนวณระยะเวลาทั้งหมดของโปรเจค
    total_days = (project_end - project_start).days
    if total_days <= 0:
        return 100  # โปรเจคสิ้นสุดแล้ว
    
    # คำนวณจำนวนวันที่ผ่านไป
    days_passed = (now - project_start).days
    
    # คำนวณเปอร์เซ็นต์ความคืบหน้า (ไม่เกิน 100%)
    progress = min(100, round((days_passed / total_days) * 100, 2))
    
    return progress

def _evaluate_test_risk(expected_progress: float, actual_progress: float, fail_rate: float) -> str:
    """
    ประเมินระดับความเสี่ยงจากความคืบหน้าของการทดสอบและอัตราการล้มเหลว
    
    Args:
        expected_progress (float): ความคืบหน้าที่คาดหวัง (%)
        actual_progress (float): ความคืบหน้าจริง (%)
        fail_rate (float): อัตราการล้มเหลว (%)
        
    Returns:
        str: ระดับความเสี่ยง ('LOW', 'MEDIUM', 'HIGH')
    """
    # คำนวณส่วนต่างระหว่างความคืบหน้าที่คาดหวังกับความคืบหน้าจริง
    progress_gap = expected_progress - actual_progress
    
    # ประเมินความเสี่ยง
    if progress_gap <= 10 and fail_rate < 5:
        return 'LOW'
    elif progress_gap <= 20 and fail_rate < 15:
        return 'MEDIUM'
    else:
        return 'HIGH'

def _calculate_test_coverage(test_data: List[Dict[str, Any]]) -> float:
    """
    คำนวณค่า test coverage โดยประมาณ
    
    Args:
        test_data (List[Dict[str, Any]]): ข้อมูลการทดสอบทั้งหมด
        
    Returns:
        float: เปอร์เซ็นต์ของ test coverage
    """
    # หมายเหตุ: การคำนวณ coverage ที่แท้จริงควรใช้เครื่องมือเฉพาะทาง
    # นี่เป็นเพียงตัวอย่างการประมาณค่าแบบง่าย
    
    # ตรวจสอบหาค่า coverage จากข้อมูลทดสอบโดยตรง (ถ้ามี)
    for test in test_data:
        if 'coverage' in test:
            try:
                return float(test['coverage'])
            except (ValueError, TypeError):
                pass
    
    # ถ้าไม่มีข้อมูล coverage โดยตรง ให้ประมาณค่าจากสัดส่วนของเทสเคสที่ passed
    total_tests = len(test_data)
    
    if total_tests == 0:
        return 0
    
    passed_tests = sum(1 for t in test_data if t.get('status', '').lower() == 'pass')
    
    # คำนวณ coverage โดยประมาณ (อาจใช้สูตรที่ซับซ้อนขึ้นในสถานการณ์จริง)
    # สมมติว่า coverage สูงสุดที่เป็นไปได้คือ 90% เพื่อสะท้อนว่าเทสแบบอัตโนมัติไม่ได้ครอบคลุม 100%
    max_possible_coverage = 90
    estimated_coverage = (passed_tests / total_tests) * max_possible_coverage
    
    return round(estimated_coverage, 2)

def _calculate_module_metrics(test_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    คำนวณเมตริกตาม module/component
    
    Args:
        test_data (List[Dict[str, Any]]): ข้อมูลการทดสอบทั้งหมด
        
    Returns:
        Dict[str, Dict[str, Any]]: เมตริกแยกตาม module
    """
    # จัดกลุ่มตาม module/component
    module_tests = defaultdict(list)
    
    for test in test_data:
        # รองรับรูปแบบ field ที่แตกต่างกัน
        module = test.get('module', test.get('component', test.get('area', 'unknown')))
        if not module:
            module = 'unknown'
        
        module_tests[module].append(test)
    
    # คำนวณเมตริกสำหรับแต่ละ module
    metrics_by_module = {}
    
    for module, tests in module_tests.items():
        total = len(tests)
        passes = sum(1 for t in tests if t.get('status', '').lower() == 'pass')
        fails = sum(1 for t in tests if t.get('status', '').lower() == 'fail')
        skips = sum(1 for t in tests if t.get('status', '').lower() in ['skip', 'skipped'])
        
        pass_rate = round((passes / total) * 100, 2) if total > 0 else 0
        fail_rate = round((fails / total) * 100, 2) if total > 0 else 0
        skip_rate = round((skips / total) * 100, 2) if total > 0 else 0
        
        metrics_by_module[module] = {
            'total_tests': total,
            'passed': passes,
            'failed': fails,
            'skipped': skips,
            'pass_rate': pass_rate,
            'fail_rate': fail_rate,
            'skip_rate': skip_rate
        }
    
    return metrics_by_module

def _calculate_defect_density(total_defects: int, code_size: Optional[int] = None) -> float:
    """
    คำนวณความหนาแน่นของข้อบกพร่อง (จำนวนข้อบกพร่องต่อขนาดโค้ด)
    
    Args:
        total_defects (int): จำนวนข้อบกพร่องทั้งหมด
        code_size (Optional[int]): ขนาดของโค้ด (บรรทัด/KLOC)
        
    Returns:
        float: ความหนาแน่นของข้อบกพร่อง
    """
    # ถ้าไม่มีข้อมูลขนาดโค้ด ให้ใช้ค่าตั้งต้น 10,000 บรรทัด
    if code_size is None:
        code_size = 10000
    
    # หลีกเลี่ยงการหารด้วย 0
    if code_size <= 0:
        return 0
    
    # คำนวณข้อบกพร่องต่อ 1,000 บรรทัดโค้ด (KLOC)
    density = (total_defects / code_size) * 1000
    
    return round(density, 2)

def _analyze_severity_distribution(defect_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    วิเคราะห์การกระจายของข้อบกพร่องตามระดับความรุนแรง
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        
    Returns:
        Dict[str, int]: จำนวนข้อบกพร่องแยกตามระดับความรุนแรง
    """
    severity_counts = defaultdict(int)
    
    for defect in defect_data:
        # รองรับรูปแบบ field ที่แตกต่างกัน
        severity = defect.get('severity', defect.get('priority', 'unknown')).lower()
        
        # แปลงค่าตัวเลขเป็นข้อความ (ถ้ามี)
        if severity == '1':
            severity = 'critical'
        elif severity == '2':
            severity = 'high'
        elif severity == '3':
            severity = 'medium'
        elif severity == '4':
            severity = 'low'
        elif severity == '5':
            severity = 'trivial'
        
        # เพิ่มจำนวน
        severity_counts[severity] += 1
    
    return dict(severity_counts)

def _analyze_status_distribution(defect_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    วิเคราะห์การกระจายของข้อบกพร่องตามสถานะ
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        
    Returns:
        Dict[str, int]: จำนวนข้อบกพร่องแยกตามสถานะ
    """
    status_counts = defaultdict(int)
    
    for defect in defect_data:
        status = defect.get('status', 'unknown').lower()
        status_counts[status] += 1
    
    return dict(status_counts)

def _calculate_defect_trends(defect_data: List[Dict[str, Any]], period_days: int = 90) -> List[Dict[str, Any]]:
    """
    คำนวณแนวโน้มของข้อบกพร่องในช่วงเวลาที่กำหนด
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        period_days (int): ช่วงเวลาย้อนหลังที่ต้องการวิเคราะห์ (วัน)
        
    Returns:
        List[Dict[str, Any]]: ข้อมูลแนวโน้มรายสัปดาห์/รายเดือน
    """
    now = datetime.now()
    start_date = now - timedelta(days=period_days)
    
    # รูปแบบวันที่ที่อาจพบในข้อมูล
    date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
    
    # เตรียมข้อมูลสำหรับช่วงเวลาที่กำหนด (ทุกสัปดาห์)
    trends = []
    num_weeks = math.ceil(period_days / 7)
    
    for i in range(num_weeks):
        week_end = now - timedelta(days=i*7)
        week_start = week_end - timedelta(days=7)
        
        opened_count = 0
        closed_count = 0
        
        for defect in defect_data:
            # ตรวจสอบวันที่สร้าง
            created_date_str = defect.get('created_date', defect.get('createdDate', defect.get('created_at', '')))
            if created_date_str:
                created_date = None
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if created_date and week_start <= created_date < week_end:
                    opened_count += 1
            
            # ตรวจสอบวันที่ปิด
            if defect.get('status', '').lower() in ['closed', 'fixed', 'resolved', 'completed', 'done']:
                closed_date_str = defect.get('closed_date', defect.get('closedDate', defect.get('resolved_date', '')))
                if closed_date_str:
                    closed_date = None
                    for fmt in date_formats:
                        try:
                            closed_date = datetime.strptime(closed_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if closed_date and week_start <= closed_date < week_end:
                        closed_count += 1
        
        # สร้างข้อมูลสำหรับช่วงนี้
        week_data = {
            'period': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
            'opened': opened_count,
            'closed': closed_count,
            'net_change': opened_count - closed_count
        }
        trends.append(week_data)
    
    # เรียงตามเวลา จากเก่าไปใหม่
    trends.reverse()
    
    return trends

def _calculate_avg_resolution_time(defect_data: List[Dict[str, Any]]) -> float:
    """
    คำนวณเวลาเฉลี่ยในการแก้ไขข้อบกพร่อง
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        
    Returns:
        float: เวลาเฉลี่ยในการแก้ไข (วัน)
    """
    resolution_times = []
    date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
    
    for defect in defect_data:
        if defect.get('status', '').lower() in ['closed', 'fixed', 'resolved', 'completed', 'done']:
            created_date_str = defect.get('created_date', defect.get('createdDate', ''))
            closed_date_str = defect.get('closed_date', defect.get('closedDate', defect.get('resolved_date', '')))
            
            if created_date_str and closed_date_str:
                created_date = None
                closed_date = None
                
                # แปลงวันที่สร้าง
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                # แปลงวันที่ปิด
                for fmt in date_formats:
                    try:
                        closed_date = datetime.strptime(closed_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                # คำนวณระยะเวลาในการแก้ไข
                if created_date and closed_date:
                    resolution_time = max(0, (closed_date - created_date).days)
                    resolution_times.append(resolution_time)
    
    # คำนวณค่าเฉลี่ย
    if resolution_times:
        return round(sum(resolution_times) / len(resolution_times), 2)
    else:
        return 0

def _calculate_defect_arrival_rate(defect_data: List[Dict[str, Any]], period_days: int = 30) -> float:
    """
    คำนวณอัตราการเข้ามาของข้อบกพร่องในช่วงเวลาที่กำหนด
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        period_days (int): ช่วงเวลาย้อนหลังที่ต้องการวิเคราะห์ (วัน)
        
    Returns:
        float: จำนวนข้อบกพร่องใหม่ต่อวัน
    """
    now = datetime.now()
    start_date = now - timedelta(days=period_days)
    
    # รูปแบบวันที่ที่อาจพบในข้อมูล
    date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
    
    # นับจำนวนข้อบกพร่องใหม่ในช่วงเวลาที่กำหนด
    new_defects_count = 0
    
    for defect in defect_data:
        created_date_str = defect.get('created_date', defect.get('createdDate', defect.get('created_at', '')))
        if created_date_str:
            created_date = None
            for fmt in date_formats:
                try:
                    created_date = datetime.strptime(created_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if created_date and created_date >= start_date:
                new_defects_count += 1
    
    # คำนวณอัตราต่อวัน
    if period_days > 0:
        return round(new_defects_count / period_days, 2)
    else:
        return 0

def _calculate_defect_close_rate(defect_data: List[Dict[str, Any]], period_days: int = 30) -> float:
    """
    คำนวณอัตราการปิดข้อบกพร่องในช่วงเวลาที่กำหนด
    
    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        period_days (int): ช่วงเวลาย้อนหลังที่ต้องการวิเคราะห์ (วัน)
        
    Returns:
        float: จำนวนข้อบกพร่องที่ปิดต่อวัน
    """
    now = datetime.now()
    start_date = now - timedelta(days=period_days)
    
    # รูปแบบวันที่ที่อาจพบในข้อมูล
    date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
    
    # นับจำนวนข้อบกพร่องที่ปิดในช่วงเวลาที่กำหนด
    closed_defects_count = 0
    
    for defect in defect_data:
        if defect.get('status', '').lower() in ['closed', 'fixed', 'resolved', 'completed', 'done']:
            closed_date_str = defect.get('closed_date', defect.get('closedDate', defect.get('resolved_date', '')))
            if closed_date_str:
                closed_date = None
                for fmt in date_formats:
                    try:
                        closed_date = datetime.strptime(closed_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if closed_date and closed_date >= start_date:
                    closed_defects_count += 1
    
    # คำนวณอัตราต่อวัน
    if period_days > 0:
        return round(closed_defects_count / period_days, 2)
    else:
        return 0 