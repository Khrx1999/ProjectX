# CORE/defect_analyzer.py

"""
Defect Analyzer Module
โมดูลสำหรับวิเคราะห์ข้อบกพร่อง (defects) ที่พบในระบบ
รวมฟังก์ชันจาก defect_analysis.py และ defect_analyzer.py เข้าด้วยกัน

Author: Tassana Khrueawan
Version: 1.1.0 (Combined Module)
"""

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

# Setup logger
logger = logging.getLogger("DefectAnalyzer")

def analyze_defects(defects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    วิเคราะห์ข้อบกพร่อง (defects) ที่พบในระบบ เพื่อหาแนวทางแก้ไขและป้องกัน

    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด

    Returns:
        Dict[str, Any]: ผลการวิเคราะห์ข้อบกพร่อง ประกอบด้วย:
            - highest_priority_defects: รายการข้อบกพร่องที่มีความสำคัญสูงสุด
            - oldest_open_defects: รายการข้อบกพร่องที่เปิดค้างนานที่สุด
            - recently_closed_defects: รายการข้อบกพร่องที่ปิดล่าสุด
            - module_distribution: การกระจายของข้อบกพร่องตามโมดูล
            - defect_velocity: ความเร็วในการแก้ไขข้อบกพร่อง
    """
    if not defects_data:
        logger.warning("ไม่มีข้อมูลข้อบกพร่องให้วิเคราะห์")
        return {
            "highest_priority_defects": [],
            "oldest_open_defects": [],
            "recently_closed_defects": [],
            "module_distribution": {},
            "defect_velocity": {
                "avg_resolution_time": 0,
                "weekly_velocity": [],
                "trend": "STABLE"
            }
        }

    try:
        # 1. หาข้อบกพร่องที่มีความสำคัญสูงสุด (priority/severity)
        highest_priority_defects = _find_highest_priority_defects(defects_data)

        # 2. หาข้อบกพร่องที่เปิดค้างนานที่สุด
        oldest_open_defects = _find_oldest_open_defects(defects_data)

        # 3. หาข้อบกพร่องที่ปิดล่าสุด
        recently_closed_defects = _find_recently_closed_defects(defects_data)

        # 4. วิเคราะห์การกระจายของข้อบกพร่องตามโมดูล
        module_distribution = _analyze_module_distribution(defects_data)

        # 5. วิเคราะห์ความเร็วในการแก้ไขข้อบกพร่อง
        defect_velocity = _calculate_defect_velocity(defects_data)

        return {
            "highest_priority_defects": highest_priority_defects,
            "oldest_open_defects": oldest_open_defects,
            "recently_closed_defects": recently_closed_defects,
            "module_distribution": module_distribution,
            "defect_velocity": defect_velocity
        }

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ข้อบกพร่อง: {str(e)}")
        return {
            "error": f"เกิดข้อผิดพลาดในการวิเคราะห์: {str(e)}",
            "highest_priority_defects": [],
            "oldest_open_defects": [],
            "recently_closed_defects": [],
            "module_distribution": {},
            "defect_velocity": {
                "avg_resolution_time": 0,
                "weekly_velocity": [],
                "trend": "UNKNOWN"
            }
        }

# ฟังก์ชันจาก defect_analysis.py
def calculate_resolution_days(reported_date: str, closed_date: Optional[str], today: Optional[datetime] = None) -> Optional[int]:
    """
    Calculate days taken to resolve a defect
    
    Args:
        reported_date (str): Date when defect was reported in "YYYY-MM-DD" format
        closed_date (Optional[str]): Date when defect was closed in "YYYY-MM-DD" format, or None if still open
        today (Optional[datetime]): Current date (used when defect is still open)
        
    Returns:
        Optional[int]: Number of days taken to resolve defect or days it has been open
    """
    if not reported_date:
        return None
    try:
        reported = datetime.strptime(reported_date, "%Y-%m-%d")
        if closed_date:
            closed = datetime.strptime(closed_date, "%Y-%m-%d")
        else:
            closed = today or datetime.now()
        days = (closed - reported).days
        return days
    except ValueError as e:
        logger.warning(f"Failed to calculate resolution days: {e}, reported_date={reported_date}, closed_date={closed_date}")
        return None

def prepare_defect_analysis_data(defects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prepare defect analysis data for reporting
    
    Args:
        defects (List[Dict[str, Any]]): List of defect dictionaries
        
    Returns:
        Dict[str, Any]: Analyzed defect data for reporting
    """
    if not defects:
        return {
            "TOTAL_DEFECTS": 0,
            "TOTAL_DEFECTS_OPEN": 0,
            "TOTAL_DEFECTS_CLOSED": 0,
            "AVG_RESOLUTION_DAYS": 0,
            "PEAK_DEFECT_COUNT": 0,
            "PEAK_DEFECT_DATE": "N/A"
        }
    
    # Count statistics
    total_defects = len(defects)
    open_defects = sum(1 for d in defects if d.get("status", "").lower() in ["open", "in progress"])
    closed_defects = total_defects - open_defects
    closed_defect_rate = (closed_defects / total_defects) * 100 if total_defects > 0 else 0
    
    # Calculate resolution times
    resolution_times = []
    for defect in defects:
        if defect.get("status", "").lower() == "closed":
            days = calculate_resolution_days(
                defect.get("reported_date"), 
                defect.get("closed_date")
            )
            if days is not None:
                resolution_times.append(days)
    
    avg_resolution_days = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # Find reporting frequency by date
    date_counts = {}
    for defect in defects:
        report_date = defect.get("reported_date")
        if report_date:
            date_counts[report_date] = date_counts.get(report_date, 0) + 1
    
    # Find peak date
    peak_date = "N/A"
    peak_count = 0
    for date, count in date_counts.items():
        if count > peak_count:
            peak_count = count
            peak_date = date
    
    # Result
    return {
        "TOTAL_DEFECTS": total_defects,
        "TOTAL_DEFECTS_OPEN": open_defects,
        "TOTAL_DEFECTS_CLOSED": closed_defects,
        "TOTAL_DEFECTS_CLOSED_PERCENT": round(closed_defect_rate, 1),
        "AVG_RESOLUTION_DAYS": round(avg_resolution_days, 1),
        "PEAK_DEFECT_COUNT": peak_count,
        "PEAK_DEFECT_DATE": peak_date
    }

def calculate_sla_metrics(defects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate SLA metrics for defects
    
    Args:
        defects (List[Dict[str, Any]]): List of defect dictionaries
        
    Returns:
        Dict[str, Any]: SLA metrics
    """
    # Default SLA days by severity
    sla_limits = {
        "critical": 3,  # 3 days for Critical
        "high": 5,      # 5 days for High
        "medium": 7,    # 7 days for Medium
        "low": 14       # 14 days for Low
    }
    
    if not defects:
        return {
            "sla_completion_rate": 0,
            "severity_metrics": []
        }
    
    closed_defects = [d for d in defects if d.get("status", "").lower() == "closed"]
    total_closed = len(closed_defects)
    
    within_sla_count = 0
    severity_metrics = []
    
    # Group defects by severity
    severity_groups = {}
    for defect in closed_defects:
        severity = defect.get("severity", "unknown").lower()
        if severity not in severity_groups:
            severity_groups[severity] = []
        severity_groups[severity].append(defect)
    
    # Calculate metrics for each severity
    for severity, defect_list in severity_groups.items():
        sla_limit = sla_limits.get(severity, 7)  # Default to 7 days if severity not defined
        
        within_sla = 0
        resolution_times = []
        
        for defect in defect_list:
            days = calculate_resolution_days(
                defect.get("reported_date"), 
                defect.get("closed_date")
            )
            if days is not None:
                resolution_times.append(days)
                if days <= sla_limit:
                    within_sla += 1
                    within_sla_count += 1
        
        avg_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        sla_rate = (within_sla / len(defect_list)) * 100 if defect_list else 0
        
        severity_metrics.append({
            "severity": severity.capitalize(),
            "count": len(defect_list),
            "avg_resolution_days": round(avg_time, 1),
            "sla_limit_days": sla_limit,
            "within_sla_count": within_sla,
            "sla_completion_rate": round(sla_rate, 1)
        })
    
    # Overall SLA completion rate
    overall_sla_rate = (within_sla_count / total_closed) * 100 if total_closed > 0 else 0
    
    return {
        "sla_completion_rate": round(overall_sla_rate, 1),
        "severity_metrics": sorted(severity_metrics, key=lambda x: x["count"], reverse=True)
    }

def get_defect_trends(defects: List[Dict[str, Any]], days: int = 30) -> Dict[str, Any]:
    """
    Get trend data for defects over a period
    
    Args:
        defects (List[Dict[str, Any]]): List of defect dictionaries
        days (int, optional): Number of days to analyze. Defaults to 30.
        
    Returns:
        Dict[str, Any]: Trend data
    """
    if not defects:
        return {
            "labels": [],
            "opened": [],
            "closed": []
        }
    
    # Find date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Initialize daily counts
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    opened_counts = {date: 0 for date in date_range}
    closed_counts = {date: 0 for date in date_range}
    
    # Count opened and closed defects by date
    for defect in defects:
        reported_date = defect.get("reported_date")
        if reported_date in opened_counts:
            opened_counts[reported_date] += 1
        
        closed_date = defect.get("closed_date")
        if closed_date and closed_date in closed_counts:
            closed_counts[closed_date] += 1
    
    # Convert to lists for charting
    opened_values = [opened_counts[date] for date in date_range]
    closed_values = [closed_counts[date] for date in date_range]
    
    return {
        "labels": date_range,
        "opened": opened_values,
        "closed": closed_values
    }

# ฟังก์ชันจาก defect_analyzer.py (เดิม)
def _find_highest_priority_defects(defects_data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    หาข้อบกพร่องที่มีความสำคัญสูงสุด
    
    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        limit (int): จำนวนข้อบกพร่องที่ต้องการ
        
    Returns:
        List[Dict[str, Any]]: รายการข้อบกพร่องที่มีความสำคัญสูงสุด
    """
    # สร้าง mapping สำหรับระดับความสำคัญ
    priority_mapping = {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
        "trivial": 5,
        "p1": 1,
        "p2": 2,
        "p3": 3,
        "p4": 4,
        "p5": 5,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "blocker": 1,
        "major": 2,
        "normal": 3,
        "minor": 4,
        "trivial": 5
    }
    
    # สถานะที่ถือว่ายังเปิดอยู่
    open_statuses = [
        "open", "in progress", "reopened", "new", 
        "active", "verified", "in review", "to do",
        "backlog"
    ]
    
    # คัดกรองเฉพาะข้อบกพร่องที่ยังเปิดอยู่
    open_defects = [
        defect for defect in defects_data 
        if isinstance(defect, dict) and 
        defect.get('status', '').lower() in open_statuses
    ]
    
    # หากไม่มีข้อบกพร่องที่เปิดอยู่ ให้ใช้ทั้งหมด
    if not open_defects:
        open_defects = [defect for defect in defects_data if isinstance(defect, dict)]
        
    # เรียงลำดับตามความสำคัญ
    sorted_defects = sorted(
        open_defects,
        key=lambda x: priority_mapping.get(
            str(x.get('priority', x.get('severity', 'medium'))).lower(), 
            3  # ค่าเริ่มต้นคือ medium (3)
        )
    )
    
    # เพิ่มข้อมูลเพิ่มเติมที่จำเป็นสำหรับการวิเคราะห์
    result = []
    for defect in sorted_defects[:limit]:
        # ข้อมูลพื้นฐานที่ต้องมี
        defect_info = {
            "id": defect.get('id', 'unknown'),
            "summary": defect.get('summary', defect.get('title', 'Unknown')),
            "priority": defect.get('priority', defect.get('severity', 'medium')),
            "status": defect.get('status', 'unknown'),
            "module": defect.get('module', defect.get('component', 'unknown')),
        }
        
        # คำนวณอายุของข้อบกพร่อง
        created_date_str = defect.get('created_date', defect.get('createdDate', ''))
        if created_date_str:
            try:
                date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                created_date = None
                
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if created_date:
                    defect_age = (datetime.now() - created_date).days
                    defect_info['age_days'] = defect_age
            except Exception:
                defect_info['age_days'] = 'unknown'
                
        # เพิ่มเมตริกความเสี่ยง (ตามลำดับความสำคัญและอายุ)
        priority_value = priority_mapping.get(
            str(defect.get('priority', defect.get('severity', 'medium'))).lower(), 
            3
        )
        
        age_days = defect_info.get('age_days', 0)
        if isinstance(age_days, str):
            age_days = 30  # ค่าเริ่มต้นถ้าไม่รู้อายุ
            
        # คำนวณคะแนนความเสี่ยง (ยิ่งสำคัญยิ่งคะแนนสูง + ยิ่งเก่ายิ่งคะแนนสูง)
        risk_score = (6 - priority_value) * 10
        if age_days > 30:
            risk_score += 10
        if age_days > 90:
            risk_score += 20
            
        defect_info['risk_score'] = risk_score
        
        result.append(defect_info)
    
    # เรียงอีกครั้งตามคะแนนความเสี่ยง
    return sorted(result, key=lambda x: x.get('risk_score', 0), reverse=True)

def _find_oldest_open_defects(defects_data: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """
    หาข้อบกพร่องที่เปิดค้างนานที่สุด
    
    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        limit (int): จำนวนข้อบกพร่องที่ต้องการ
        
    Returns:
        List[Dict[str, Any]]: รายการข้อบกพร่องที่เปิดค้างนานที่สุด
    """
    # สถานะที่ถือว่ายังเปิดอยู่
    open_statuses = [
        "open", "in progress", "reopened", "new", 
        "active", "verified", "in review", "to do",
        "backlog"
    ]
    
    # คัดกรองเฉพาะข้อบกพร่องที่ยังเปิดอยู่
    open_defects = []
    for defect in defects_data:
        if isinstance(defect, dict) and defect.get('status', '').lower() in open_statuses:
            created_date = None
            created_date_str = defect.get('created_date', defect.get('createdDate', ''))
            
            if created_date_str:
                date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
            
            if created_date:
                defect_with_age = defect.copy()
                defect_with_age['created_date_obj'] = created_date
                defect_with_age['age_days'] = (datetime.now() - created_date).days
                open_defects.append(defect_with_age)
    
    # เรียงลำดับตามวันที่สร้าง (จากเก่าไปใหม่)
    sorted_defects = sorted(
        open_defects,
        key=lambda x: x.get('created_date_obj', datetime.now()),
    )
    
    # สร้างผลลัพธ์
    result = []
    for defect in sorted_defects[:limit]:
        defect_info = {
            "id": defect.get('id', 'unknown'),
            "summary": defect.get('summary', defect.get('title', 'Unknown')),
            "priority": defect.get('priority', defect.get('severity', 'medium')),
            "status": defect.get('status', 'unknown'),
            "module": defect.get('module', defect.get('component', 'unknown')),
            "created_date": defect.get('created_date', defect.get('createdDate', 'unknown')),
            "age_days": defect.get('age_days', 'unknown')
        }
        result.append(defect_info)
    
    return result

def _find_recently_closed_defects(defects_data: List[Dict[str, Any]], limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
    """
    หาข้อบกพร่องที่ปิดล่าสุด
    
    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        limit (int): จำนวนข้อบกพร่องที่ต้องการ
        days (int): จำนวนวันย้อนหลังที่ต้องการดู
        
    Returns:
        List[Dict[str, Any]]: รายการข้อบกพร่องที่ปิดล่าสุด
    """
    # สถานะที่ถือว่าปิดแล้ว
    closed_statuses = [
        "closed", "fixed", "resolved", "completed", "done", 
        "verified", "delivered", "released"
    ]
    
    # คัดกรองเฉพาะข้อบกพร่องที่ปิดแล้ว
    closed_defects = []
    now = datetime.now()
    min_date = now - timedelta(days=days)
    
    for defect in defects_data:
        if isinstance(defect, dict) and defect.get('status', '').lower() in closed_statuses:
            closed_date = None
            closed_date_str = defect.get('closed_date', defect.get('closedDate', 
                            defect.get('resolved_date', defect.get('resolvedDate', ''))))
            
            if not closed_date_str:
                # ถ้าไม่มีวันที่ปิด แต่สถานะคือปิด ให้ใช้วันที่อัปเดตล่าสุด
                closed_date_str = defect.get('updated_date', defect.get('updatedDate', ''))
            
            if closed_date_str:
                date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                
                for fmt in date_formats:
                    try:
                        closed_date = datetime.strptime(closed_date_str, fmt)
                        break
                    except ValueError:
                        continue
            
            if closed_date and closed_date >= min_date:
                defect_with_close_date = defect.copy()
                defect_with_close_date['closed_date_obj'] = closed_date
                closed_defects.append(defect_with_close_date)
    
    # เรียงลำดับตามวันที่ปิด (จากใหม่ไปเก่า)
    sorted_defects = sorted(
        closed_defects,
        key=lambda x: x.get('closed_date_obj', datetime.now()),
        reverse=True
    )
    
    # สร้างผลลัพธ์
    result = []
    for defect in sorted_defects[:limit]:
        defect_info = {
            "id": defect.get('id', 'unknown'),
            "summary": defect.get('summary', defect.get('title', 'Unknown')),
            "priority": defect.get('priority', defect.get('severity', 'medium')),
            "status": defect.get('status', 'unknown'),
            "module": defect.get('module', defect.get('component', 'unknown')),
            "closed_date": defect.get('closed_date', defect.get('closedDate', 
                          defect.get('resolved_date', defect.get('resolvedDate', 'unknown')))),
            "resolution": defect.get('resolution', 'fixed')
        }
        
        # ถ้ามีข้อมูลวันที่สร้าง ให้คำนวณระยะเวลาในการแก้ไข
        created_date_str = defect.get('created_date', defect.get('createdDate', ''))
        if created_date_str:
            created_date = None
            date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
            
            for fmt in date_formats:
                try:
                    created_date = datetime.strptime(created_date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if created_date and defect.get('closed_date_obj'):
                resolution_days = (defect['closed_date_obj'] - created_date).days
                defect_info['resolution_days'] = max(0, resolution_days)
        
        result.append(defect_info)
    
    return result

def _analyze_module_distribution(defects_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    วิเคราะห์การกระจายของข้อบกพร่องตามโมดูล
    
    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        
    Returns:
        Dict[str, Dict[str, Any]]: ข้อมูลการกระจายของข้อบกพร่องตามโมดูล
    """
    # จัดกลุ่มตามโมดูล
    module_defects = defaultdict(list)
    
    for defect in defects_data:
        if isinstance(defect, dict):
            # รองรับหลายรูปแบบของฟิลด์โมดูล
            module = defect.get('module', defect.get('component', defect.get('area', 'unknown')))
            if not module:
                module = 'unknown'
            
            module_defects[module].append(defect)
    
    # สถานะที่ถือว่ายังเปิดอยู่
    open_statuses = [
        "open", "in progress", "reopened", "new", 
        "active", "verified", "in review", "to do",
        "backlog"
    ]
    
    # วิเคราะห์แต่ละโมดูล
    results = {}
    
    for module, defects in module_defects.items():
        total = len(defects)
        open_count = sum(1 for d in defects if d.get('status', '').lower() in open_statuses)
        closed_count = total - open_count
        
        # นับตามความรุนแรง
        severity_counts = Counter()
        for defect in defects:
            severity = str(defect.get('priority', defect.get('severity', 'medium'))).lower()
            severity_counts[severity] += 1
        
        # วิเคราะห์แนวโน้ม (จำนวนข้อบกพร่องในช่วง 3 เดือนล่าสุด)
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        monthly_counts = [0, 0, 0]  # 3 เดือนล่าสุด
        
        for defect in defects:
            created_date_str = defect.get('created_date', defect.get('createdDate', ''))
            if created_date_str:
                created_date = None
                date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
                
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if created_date and created_date >= three_months_ago:
                    month_index = min(2, (now.year - created_date.year) * 12 + (now.month - created_date.month))
                    monthly_counts[month_index] += 1
        
        # กำหนดแนวโน้ม
        if monthly_counts[0] > monthly_counts[1] > monthly_counts[2]:
            trend = "INCREASING"
        elif monthly_counts[0] < monthly_counts[1] < monthly_counts[2]:
            trend = "DECREASING"
        else:
            trend = "STABLE"
        
        results[module] = {
            "total_defects": total,
            "open_defects": open_count,
            "closed_defects": closed_count,
            "severity_distribution": dict(severity_counts),
            "monthly_trend": monthly_counts,
            "trend": trend,
            "risk_factor": _calculate_module_risk_factor(total, open_count, severity_counts)
        }
    
    # เพิ่มแนวโน้มรวม
    total_modules = len(results)
    if total_modules > 0:
        increasing_modules = sum(1 for info in results.values() if info.get('trend') == 'INCREASING')
        decreasing_modules = sum(1 for info in results.values() if info.get('trend') == 'DECREASING')
        
        if increasing_modules > decreasing_modules:
            overall_trend = "INCREASING"
        elif decreasing_modules > increasing_modules:
            overall_trend = "DECREASING"
        else:
            overall_trend = "STABLE"
        
        # เพิ่มสรุปรวม
        results['summary'] = {
            "total_modules": total_modules,
            "increasing_modules": increasing_modules,
            "decreasing_modules": decreasing_modules,
            "stable_modules": total_modules - increasing_modules - decreasing_modules,
            "overall_trend": overall_trend
        }
    
    return results

def _calculate_module_risk_factor(total: int, open_count: int, severity_counts: Counter) -> float:
    """
    คำนวณปัจจัยความเสี่ยงของโมดูล
    
    Args:
        total (int): จำนวนข้อบกพร่องทั้งหมด
        open_count (int): จำนวนข้อบกพร่องที่ยังเปิดอยู่
        severity_counts (Counter): การนับตามความรุนแรง
        
    Returns:
        float: ค่าปัจจัยความเสี่ยง (0.0-1.0)
    """
    if total == 0:
        return 0.0
    
    # ปัจจัยจากสัดส่วนข้อบกพร่องที่ยังเปิดอยู่
    open_factor = open_count / total
    
    # ปัจจัยจากความรุนแรง (ให้น้ำหนักกับข้อบกพร่องที่มีความรุนแรงสูง)
    severity_factor = 0
    severity_mapping = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
        "trivial": 0.1,
        "p1": 1.0,
        "p2": 0.8,
        "p3": 0.5,
        "p4": 0.2,
        "p5": 0.1,
        "1": 1.0,
        "2": 0.8,
        "3": 0.5,
        "4": 0.2,
        "5": 0.1,
        "blocker": 1.0,
        "major": 0.8,
        "normal": 0.5,
        "minor": 0.2,
        "trivial": 0.1
    }
    
    for severity, count in severity_counts.items():
        weight = severity_mapping.get(severity.lower(), 0.5)
        severity_factor += (count / total) * weight
    
    # รวมปัจจัยทั้งหมด (ให้น้ำหนักกับสัดส่วนที่เปิดอยู่มากกว่า)
    risk_factor = (open_factor * 0.6) + (severity_factor * 0.4)
    
    return round(risk_factor, 2)

def _calculate_defect_velocity(defects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    คำนวณความเร็วในการแก้ไขข้อบกพร่อง
    
    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        
    Returns:
        Dict[str, Any]: ข้อมูลความเร็วในการแก้ไขข้อบกพร่อง
    """
    # สถานะที่ถือว่าปิดแล้ว
    closed_statuses = [
        "closed", "fixed", "resolved", "completed", "done", 
        "verified", "delivered", "released"
    ]
    
    # ข้อมูลสำหรับคำนวณเวลาเฉลี่ยในการแก้ไข
    resolution_times = []
    date_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"]
    
    # ข้อมูลเปิด/ปิดรายสัปดาห์
    weekly_data = defaultdict(lambda: {"opened": 0, "closed": 0})
    now = datetime.now()
    
    # วนลูปเพื่อวิเคราะห์ข้อบกพร่องแต่ละรายการ
    for defect in defects_data:
        if isinstance(defect, dict):
            # คำนวณเวลาในการแก้ไข (เฉพาะที่ปิดแล้ว)
            if defect.get('status', '').lower() in closed_statuses:
                created_date_str = defect.get('created_date', defect.get('createdDate', ''))
                closed_date_str = defect.get('closed_date', defect.get('closedDate', 
                                    defect.get('resolved_date', defect.get('resolvedDate', ''))))
                
                if created_date_str and closed_date_str:
                    created_date = None
                    closed_date = None
                    
                    # พยายามแปลงวันที่สร้าง
                    for fmt in date_formats:
                        try:
                            created_date = datetime.strptime(created_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    # พยายามแปลงวันที่ปิด
                    for fmt in date_formats:
                        try:
                            closed_date = datetime.strptime(closed_date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    # เพิ่มเวลาในการแก้ไข
                    if created_date and closed_date:
                        resolution_time = (closed_date - created_date).days
                        if resolution_time >= 0:  # กันกรณีวันที่ผิดพลาด
                            resolution_times.append(resolution_time)
                            
                            # บันทึกข้อมูลรายสัปดาห์ (ปิด)
                            week_key = closed_date.strftime("%Y-W%U")
                            weekly_data[week_key]["closed"] += 1
            
            # บันทึกข้อมูลรายสัปดาห์ (เปิด)
            created_date_str = defect.get('created_date', defect.get('createdDate', ''))
            if created_date_str:
                created_date = None
                for fmt in date_formats:
                    try:
                        created_date = datetime.strptime(created_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if created_date:
                    week_key = created_date.strftime("%Y-W%U")
                    weekly_data[week_key]["opened"] += 1
    
    # คำนวณเวลาเฉลี่ยในการแก้ไข
    avg_resolution_time = 0
    if resolution_times:
        avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1)
    
    # แปลงข้อมูลรายสัปดาห์เป็นรายการและเรียงตามวันที่
    weekly_velocity = []
    for week_key, counts in sorted(weekly_data.items()):
        year_str, week_str = week_key.split("-W")
        year = int(year_str)
        week = int(week_str)
        
        # คำนวณวันแรกของสัปดาห์ (อาจมีความไม่แม่นยำเล็กน้อยแต่ใช้งานได้)
        first_day = datetime.strptime(f"{year}-{week}-1", "%Y-%U-%w")
        
        weekly_velocity.append({
            "week": week_key,
            "period": f"{first_day.strftime('%Y-%m-%d')} to {(first_day + timedelta(days=6)).strftime('%Y-%m-%d')}",
            "opened": counts["opened"],
            "closed": counts["closed"],
            "net": counts["closed"] - counts["opened"]
        })
    
    # แสดงเฉพาะ 12 สัปดาห์ล่าสุด
    weekly_velocity = weekly_velocity[-12:] if len(weekly_velocity) > 12 else weekly_velocity
    
    # วิเคราะห์แนวโน้ม
    trend = "STABLE"
    if len(weekly_velocity) >= 4:
        recent_net = sum(week["net"] for week in weekly_velocity[-4:])
        if recent_net > 0:
            trend = "IMPROVING"  # ปิดมากกว่าเปิด
        elif recent_net < 0:
            trend = "DECLINING"  # เปิดมากกว่าปิด
    
    return {
        "avg_resolution_time": avg_resolution_time,
        "weekly_velocity": weekly_velocity,
        "trend": trend
    } 