"""
Defect Trend Prepare Module
รับผิดชอบการเตรียมข้อมูลแนวโน้มและการวิเคราะห์ข้อบกพร่อง

Author: Tassana Khrueawan
Version: 2.1.3 (No Banner and Top Log)
"""

from robot.api import logger
from datetime import datetime, timedelta
import os
import sys
import json
from typing import Dict, Any, Optional, List
from collections import defaultdict, Counter

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from UTILS import get_logger
from CORE.defect_analyzer import analyze_defects, prepare_defect_analysis_data, calculate_sla_metrics, get_defect_trends

# Setup logger
logger = get_logger("DefectTrendPrepare")

def prepare_defect_trend_analysis_data(defects_data: Any = None, defects_file: str = None) -> Dict[str, Any]:
    """
    เตรียมข้อมูล Defect Trend Analysis โดยรองรับ input ทั้ง
    - list ของ defects
    - dict ที่มีคีย์ 'defects'
    - path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects
    
    Args:
        defects_data (Any, optional): ข้อมูล defects ที่โหลดมาแล้ว (list หรือ dict ที่มีคีย์ 'defects')
        defects_file (str, optional): Path ไปยังไฟล์ JSON ที่เก็บข้อมูล Defects

    Returns:
        Dict[str, Any]: Dictionary ที่มีข้อมูล Defect Trend Analysis พร้อมสำหรับใช้ใน Template
    """
    try:
        # 1. Normalize defects_data - รองรับหลายรูปแบบข้อมูล
        if isinstance(defects_data, dict) and "defects" in defects_data:
            defects_data = defects_data.get("defects", [])
        elif isinstance(defects_data, str) and os.path.exists(defects_data):
            # กรณีส่ง path มาแทน defects_file
            with open(defects_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "defects" in data:
                    defects_data = data["defects"]
                elif isinstance(data, list):
                    defects_data = data
                else:
                    defects_data = []
        elif not defects_data and defects_file:
            if not os.path.exists(defects_file):
                logger.error(f"❌ ไม่พบไฟล์ defects data: {defects_file}")
                return {}
                
            try:
                with open(defects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # รองรับหลากหลายรูปแบบข้อมูล
                if isinstance(data, list):
                    defects_data = data
                elif isinstance(data, dict):
                    if "defects" in data and isinstance(data["defects"], list):
                        defects_data = data["defects"]
                    else:
                        # หาคีย์แรกที่เป็น list
                        for key, value in data.items():
                            if isinstance(value, list) and value:
                                defects_data = value
                                break
                        
                        if not defects_data:
                            # แปลง dict เป็น list of dict items
                            defects_data = []
                            for key, value in data.items():
                                if isinstance(value, dict):
                                    value['id'] = key
                                    defects_data.append(value)
                                else:
                                    defects_data.append({'id': key, 'data': value})
                
                logger.info(f"⏳ โหลดข้อมูล defects จาก: {defects_file} (จำนวน {len(defects_data)} รายการ)")
            except Exception as e:
                logger.error(f"❌ ไม่สามารถโหลดข้อมูล defects: {str(e)}")
                return {}
        
        if not defects_data:
            logger.warning("⚠️ ไม่มีข้อมูล defects สำหรับการเตรียม Defect Trend Analysis")
            defects_data = []
        
        # 2. เตรียมข้อมูล Defect Trend Analysis
        logger.info(f"⏳ เริ่มเตรียมข้อมูลแนวโน้มข้อบกพร่อง... (จำนวน {len(defects_data)} รายการ)")
        
        # นับจำนวนตามสถานะจริงในข้อมูล
        status_counter = Counter()
        statuses_original = set()
        for defect in defects_data:
            status = (defect.get("status", "") or "").strip()
            statuses_original.add(status)
            display_status = status  # ใช้ค่าตามที่มีในข้อมูลจริง
            status_counter[display_status] += 1
        
        # คำนวณเมตริกจากข้อมูล defects (ไม่จำเป็นต้องมี test metrics สำหรับวิเคราะห์ trend)
        defect_metrics = calculate_defect_metrics(defects_data, 0)
        
        # วิเคราะห์ข้อมูล defects เชิงลึก
        defect_analysis = analyze_defects(defects_data)
        
        # ข้อมูล defect trend
        defect_trend_data = get_defect_trends(defects_data, days=56)  # 8 สัปดาห์ = 56 วัน
        
        # สถานะที่ถือว่ายังเปิดอยู่
        open_statuses = ['open', 'in progress', 'reopened', 'new', 'ready to test', 'implementation complete']
        closed_statuses = ['closed', 'fixed', 'resolved', 'completed', 'done']
        
        # นับจำนวนข้อบกพร่องที่ยังเปิดอยู่และปิดแล้ว
        total_defects = len(defects_data)
        total_defects_open = 0
        total_defects_closed = 0
        
        for defect in defects_data:
            status = (defect.get('status', '') or '').strip().lower()
            if status in closed_statuses or defect.get('closedDate'):
                total_defects_closed += 1
            else:
                total_defects_open += 1
        
        # วันที่พบข้อบกพร่องมากที่สุด
        defect_by_date = {}
        for defect in defects_data:
            create_date = defect.get('createDate', defect.get('created_date', defect.get('reportedDate', '')))
            if create_date:
                defect_by_date[create_date] = defect_by_date.get(create_date, 0) + 1
        
        peak_defect_date = max(defect_by_date.items(), key=lambda x: x[1], default=('N/A', 0))
        
        # คำนวณสัดส่วนข้อบกพร่องที่ปิดแล้ว
        total_defects_closed_percent = (total_defects_closed / total_defects) * 100 if total_defects > 0 else 0
        
        # จำนวนข้อบกพร่องตามความรุนแรง
        severity_counts = defaultdict(int)
        for defect in defects_data:
            severity = defect.get('severity', 'Unknown')
            severity_counts[severity] += 1
        
        # จำนวนข้อบกพร่องที่ยังเปิดอยู่ตามความรุนแรง
        critical_open_count = sum(1 for d in defects_data if d.get('severity', '').lower() in ['critical', 'p1', '1'] and d.get('status', '').lower() in open_statuses)
        
        # สัดส่วนข้อบกพร่องที่ยังเปิดอยู่
        open_defect_ratio = (total_defects_open / total_defects) * 100 if total_defects > 0 else 0
        
        # สัดส่วนข้อบกพร่องวิกฤตที่ยังเปิดอยู่
        critical_open_ratio = (critical_open_count / total_defects_open) * 100 if total_defects_open > 0 else 0
        
        # อายุเฉลี่ยของข้อบกพร่องที่ยังเปิดอยู่
        open_defect_ages = []
        for defect in defects_data:
            if defect.get('status', '').lower() in open_statuses:
                create_date = defect.get('createDate', defect.get('created_date', defect.get('reportedDate', '')))
                if create_date:
                    try:
                        date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                        create_date_obj = None
                        
                        for fmt in date_formats:
                            try:
                                create_date_obj = datetime.strptime(create_date, fmt)
                                break
                            except ValueError:
                                continue
                                
                        if create_date_obj:
                            age_days = (datetime.now() - create_date_obj).days
                            open_defect_ages.append(age_days)
                    except ValueError:
                        pass
        
        avg_open_defect_age = sum(open_defect_ages) / len(open_defect_ages) if open_defect_ages else 0
        avg_open_age_ratio = min(100, (avg_open_defect_age / 30) * 100) if avg_open_defect_age > 0 else 0  # เทียบกับ 30 วัน
        
        # อัตราการปิดข้อบกพร่อง
        defect_closure_rate = defect_metrics.get('defect_close_rate', 0)
        closure_rate_ratio = min(100, (defect_closure_rate / 5) * 100) if defect_closure_rate > 0 else 0  # เทียบกับ 5 ข้อ/วัน
        
        # ข้อมูลวิเคราะห์แยกตามโมดูล
        module_defect_counts = defaultdict(int)
        module_open_defect_counts = defaultdict(int)
        
        for defect in defects_data:
            module = defect.get('module', 'Unknown')
            module_defect_counts[module] += 1
            if defect.get('status', '').lower() in open_statuses:
                module_open_defect_counts[module] += 1
        
        # โมดูลที่มีข้อบกพร่องเปิดมากที่สุด
        module_with_most_open_defects = max(module_open_defect_counts.items(), key=lambda x: x[1], default=('N/A', 0))
        
        # แปลงข้อมูล trend เป็น JSON string สำหรับ JavaScript
        defect_trend_labels = json.dumps(defect_trend_data.get('labels', []))
        defect_trend_opened = json.dumps(defect_trend_data.get('opened', []))
        defect_trend_closed = json.dumps(defect_trend_data.get('closed', []))
        
        # สร้าง combined structure สำหรับ log
        defect_trend_labels_list = defect_trend_data.get('labels', [])
        defect_trend_opened_list = defect_trend_data.get('opened', [])
        defect_trend_closed_list = defect_trend_data.get('closed', [])
        defect_trend_combined_data = [
            {
                "DEFECT_TREND_DATE": d,
                "DEFECT_TREND_OPENED": defect_trend_opened_list[i] if i < len(defect_trend_opened_list) else 0,
                "DEFECT_TREND_CLOSED": defect_trend_closed_list[i] if i < len(defect_trend_closed_list) else 0,
            }
            for i, d in enumerate(defect_trend_labels_list)
        ]

        # ตรวจสอบความรุนแรงที่ใช้เวลาแก้ไขเฉลี่ยมากที่สุด
        severity_resolution_times = defaultdict(list)
        for defect in defects_data:
            if defect.get('status', '').lower() in ['closed', 'fixed', 'resolved', 'completed', 'done']:
                severity = defect.get('severity', 'Unknown')
                create_date = defect.get('createDate', defect.get('created_date', defect.get('reportedDate', '')))
                close_date = defect.get('closedDate', defect.get('closed_date', ''))
                
                if create_date and close_date:
                    try:
                        date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                        create_date_obj = None
                        close_date_obj = None
                        
                        for fmt in date_formats:
                            try:
                                create_date_obj = datetime.strptime(create_date, fmt)
                                break
                            except ValueError:
                                continue
                                
                        for fmt in date_formats:
                            try:
                                close_date_obj = datetime.strptime(close_date, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if create_date_obj and close_date_obj:
                            resolution_days = (close_date_obj - create_date_obj).days
                            severity_resolution_times[severity].append(resolution_days)
                    except ValueError:
                        pass
        
        # หาเวลาเฉลี่ยในการแก้ไขตามความรุนแรง
        avg_time_by_severity = {}
        for severity, times in severity_resolution_times.items():
            if times:
                avg_time_by_severity[severity] = sum(times) / len(times)
        
        # ความรุนแรงที่ใช้เวลาแก้ไขเฉลี่ยมากที่สุด
        severity_for_avg_time = max(avg_time_by_severity.items(), key=lambda x: x[1], default=('N/A', 0))
        
        # Defect time ranges - หาวันที่เก่าที่สุดและล่าสุดที่มีการสร้าง defect
        first_defect = min((d.get('createDate', d.get('created_date', d.get('reportedDate', '9999-12-31'))) 
                           for d in defects_data if d.get('createDate') or d.get('created_date') or d.get('reportedDate')), 
                           default='N/A')
        
        last_defect = max((d.get('createDate', d.get('created_date', d.get('reportedDate', '0000-01-01'))) 
                           for d in defects_data if d.get('createDate') or d.get('created_date') or d.get('reportedDate')), 
                           default='N/A')
        
        # สร้างข้อมูล defect_trend_data
        defect_trend_result = {
            # ข้อมูลพื้นฐาน Defects
            'TOTAL_DEFECTS': total_defects,
            'TOTAL_DEFECTS_OPEN': total_defects_open,
            'TOTAL_DEFECTS_CLOSED': total_defects_closed,
            'TOTAL_DEFECTS_CLOSED_PERCENT': round(total_defects_closed_percent, 1),
            'STATUS_COUNTS': dict(status_counter),
            
            # ข้อมูล Defect Peak
            'PEAK_DEFECT_DATE': peak_defect_date[0],
            'PEAK_DEFECT_COUNT': peak_defect_date[1],
            
            # ข้อมูลเวลาเฉลี่ยในการแก้ไข
            'AVG_FIX_TIME_DAYS': defect_metrics.get('avg_resolution_time', 0),
            'SEVERITY_FOR_AVG_TIME': severity_for_avg_time[0],
            'AVG_FIX_TIME_FOR_SEVERITY': round(severity_for_avg_time[1], 1),
            
            # ข้อมูลตามโมดูล
            'MODULE_WITH_MOST_OPEN_DEFECTS': module_with_most_open_defects[0],
            'MOST_OPEN_DEFECTS_COUNT': module_with_most_open_defects[1],
            
            # ข้อมูล metrics สำหรับกราฟ
            'OPEN_DEFECT_RATIO': round(open_defect_ratio, 1),
            'CRITICAL_OPEN_COUNT': critical_open_count,
            'CRITICAL_OPEN_RATIO': round(critical_open_ratio, 1),
            'AVG_OPEN_DEFECT_AGE': round(avg_open_defect_age, 1),
            'AVG_OPEN_AGE_RATIO': round(avg_open_age_ratio, 1),
            'DEFECT_CLOSURE_RATE': round(defect_closure_rate, 2),
            'CLOSURE_RATE_RATIO': round(closure_rate_ratio, 1),
            
            # ข้อมูล trend สำหรับกราฟ
            'DEFECT_TREND_LABELS': defect_trend_labels,
            'DEFECT_TREND_OPENED': defect_trend_opened,
            'DEFECT_TREND_CLOSED': defect_trend_closed,
            'DEFECT_TREND_COMBINED': defect_trend_combined_data,
            
            # ข้อมูลช่วงเวลา
            'DEFECT_START_DATE': first_defect,
            'DEFECT_END_DATE': last_defect,
            
            # ข้อมูลอื่นๆ
            'defect_metrics': defect_metrics,
            'defect_analysis': defect_analysis
        }
        
        # ICON MAPPING for statuses
        status_icon_map = {
            'open': '🔴', 'in progress': '🟡', 'reopened': '🔁', 'new': '🆕',
            'ready to test': '🟦', 'ready to dev': '⚪', 'implemented': '🟣',
            'implementation complete': '👨‍💻',
            'closed': '✅', 'fixed': '🟢', 'resolved': '🟢', 'completed': '🟢', 'done': '🟢',
        }
        
        def get_status_icon(statusname):
            return status_icon_map.get(statusname.strip().lower(), '•')
        
        # Flat key-value summary (mimic prepare_test_summary_data style)
        logger.info("✅ สรุป Defect Trend Analysis Data:")
        for k, v in defect_trend_result.items():
            if k in ["DEFECT_TREND_LABELS", "DEFECT_TREND_OPENED", "DEFECT_TREND_CLOSED"]:
                # ข้ามการแสดงผลอาร์เรย์แยกกัน
                continue
            elif k not in ['defect_metrics', 'defect_analysis', 'STATUS_COUNTS', 'DEFECT_TREND_COMBINED']:
                logger.info(f"  {k}: {v}")
            elif k == 'STATUS_COUNTS':
                logger.info(f"  {k}: {{{', '.join([f'{sk}: {sv}' for sk, sv in v.items()])}}}")
            elif k == 'DEFECT_TREND_COMBINED':
                # แสดงข้อมูล trend แบบรวม
                logger.info(f"  DEFECT_TREND_DATA: {v}")

        logger.info("✅ เสร็จสิ้นการเตรียม Defect Trend Analysis Data")
        
        return defect_trend_result
        
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการเตรียม Defect Trend Analysis Data: {str(e)}")
        return {}

def calculate_defect_metrics(defect_data: List[Dict[str, Any]], total_tests: int = 0) -> Dict[str, Any]:
    """
    คำนวณเมตริกต่างๆ เกี่ยวกับข้อบกพร่อง (defects) ที่จำเป็นสำหรับการวิเคราะห์แนวโน้ม

    Args:
        defect_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        total_tests (int): จำนวนข้อทดสอบทั้งหมด (ใช้สำหรับคำนวณ defect density)

    Returns:
        Dict[str, Any]: เมตริกต่างๆ เกี่ยวกับข้อบกพร่อง
    """
    if not defect_data:
        return {
            'total_defects': 0,
            'open_defects': 0,
            'closed_defects': 0,
            'defect_density': 0,
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
        defect_density = calculate_defect_density(total_defects, total_tests)
        
        # เวลาเฉลี่ยในการแก้ไข
        avg_resolution_time = calculate_avg_resolution_time(defect_data)
        
        # อัตราการเข้ามาของข้อบกพร่อง (ช่วง 30 วันล่าสุด)
        defect_arrival_rate = calculate_defect_arrival_rate(defect_data)
        
        # อัตราการปิดข้อบกพร่อง (ช่วง 30 วันล่าสุด)
        defect_close_rate = calculate_defect_close_rate(defect_data)
        
        return {
            'total_defects': total_defects,
            'open_defects': open_defects,
            'closed_defects': closed_defects,
            'defect_density': defect_density,
            'avg_resolution_time': avg_resolution_time,
            'defect_arrival_rate': defect_arrival_rate,
            'defect_close_rate': defect_close_rate
        }
    
    except Exception as e:
        logger.error(f"❌ เกิดข้อผิดพลาดในการคำนวณเมตริกข้อบกพร่อง: {str(e)}")
        return {
            'total_defects': 0,
            'open_defects': 0,
            'closed_defects': 0,
            'defect_density': 0,
            'avg_resolution_time': 0,
            'defect_arrival_rate': 0,
            'defect_close_rate': 0
        }

def calculate_defect_density(total_defects: int, code_size: Optional[int] = None) -> float:
    """
    คำนวณความหนาแน่นของข้อบกพร่อง (จำนวนข้อบกพร่องต่อขนาดโค้ด)
    
    Args:
        total_defects (int): จำนวนข้อบกพร่องทั้งหมด
        code_size (Optional[int]): ขนาดของโค้ด (บรรทัด/KLOC) หรือจำนวน test cases
        
    Returns:
        float: ความหนาแน่นของข้อบกพร่อง
    """
    # ถ้าไม่มีข้อมูลขนาดโค้ด ให้ใช้ค่าตั้งต้น 10,000 บรรทัด
    if code_size is None or code_size <= 0:
        code_size = 10000
    
    # คำนวณข้อบกพร่องต่อ 1,000 บรรทัดโค้ด (KLOC)
    density = (total_defects / code_size) * 1000
    
    return round(density, 2)

def calculate_avg_resolution_time(defect_data: List[Dict[str, Any]]) -> float:
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
            created_date_str = defect.get('created_date', defect.get('createdDate', defect.get('reportedDate', '')))
            closed_date_str = defect.get('closed_date', defect.get('closedDate', ''))
            
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

def calculate_defect_arrival_rate(defect_data: List[Dict[str, Any]], period_days: int = 30) -> float:
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
        created_date_str = defect.get('created_date', defect.get('createdDate', defect.get('reportedDate', '')))
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

def calculate_defect_close_rate(defect_data: List[Dict[str, Any]], period_days: int = 30) -> float:
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
            closed_date_str = defect.get('closed_date', defect.get('closedDate', ''))
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
