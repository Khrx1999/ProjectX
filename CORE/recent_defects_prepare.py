"""
Recent Defects Prepare Module
รับผิดชอบการเตรียมข้อมูลข้อบกพร่องล่าสุด

Author: Tassana Khrueawan
Version: 1.0.1 (Logging Style Update)
"""

from typing import Dict, Any, List
from datetime import datetime
from robot.api import logger
import os
import sys

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger

logger = get_logger("RecentDefectsPrepare")

def prepare_recent_defects_data(defects_data: List[Dict[str, Any]], limit: int = 15) -> Dict[str, Any]:
    """
    เตรียมข้อมูล Recent Defects โดยเฉพาะ
    - แสดงข้อบกพร่องล่าสุดพร้อมรายละเอียด (เรียงตามวันที่ reported ล่าสุด)

    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด
        limit (int): จำนวนข้อบกพร่องล่าสุดที่ต้องการแสดง

    Returns:
        Dict[str, Any]: Dictionary ที่มีข้อมูล Recent Defects
    """
    try:
        # Icon map for severity and status
        SEVERITY_ICON = {
            'Critical': '🔥', 'Major': '⚠️', 'Moderate': '🔶', 
            'Minor': '🔹', 'Trivial': '⬇️', 'Unknown': '❓',
        }
        STATUS_ICON = {
            'Open': '🔴', 'In progress': '🟡', 'Reopened': '🔁',
            'New': '🆕', 'Ready to test': '🟦', 'Ready to dev': '⚪',
            'Closed': '✅', 'Fixed': '🟢', 'Resolved': '🟢',
            'Completed': '🟢', 'Done': '🟢',
        }
        logger.info("—— ผลรวม Recent Defects ——")

        if not defects_data:
            logger.warning("⚠️ ไม่มีข้อมูล defects สำหรับ Recent Defects")
            logger.info("✅ เตรียมข้อมูล Recent Defects เรียบร้อยแล้ว (ข้อมูลว่าง)")
            return {"recent_defects": []}
            
        # ฟังก์ชันช่วยแปลงวันที่
        def parse_date(date_str):
            if not date_str:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"): # เพิ่ม format อื่นๆ ถ้าจำเป็น
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    pass
            logger.warning(f"ไม่สามารถแปลงวันที่: {date_str}")
            return None

        # เพิ่ม reported_date_obj เพื่อใช้เรียงลำดับ
        defects_with_date = []
        for defect in defects_data:
            reported_date_str = defect.get('reportedDate', defect.get('created_date', ''))
            reported_date_obj = parse_date(reported_date_str)
            defect_copy = defect.copy()
            defect_copy['reported_date_obj'] = reported_date_obj if reported_date_obj else datetime.min
            defects_with_date.append(defect_copy)
                
        # เรียงลำดับตามวันที่ reported (ล่าสุดมาก่อน)
        sorted_defects = sorted(defects_with_date, key=lambda x: x['reported_date_obj'], reverse=True)
        
        # เลือกตามจำนวน limit และจัดรูปแบบข้อมูล
        recent_defects_list = []
        for defect in sorted_defects[:limit]:
            sev = str(defect.get('severity', 'Unknown')).capitalize()
            status = str(defect.get('status', 'Unknown')).capitalize()
            recent_defect = {
                'id': defect.get('issueId', defect.get('id', 'N/A')),
                'description': defect.get('description', 'No description'),
                'severity': sev,
                'status': status,
                'module': defect.get('module', 'Unknown'),
                'reportedDate': defect.get('reportedDate', 'N/A'),
                # สามารถเพิ่ม field อื่นๆ ที่ต้องการแสดงใน template ได้
            }
            recent_defects_list.append(recent_defect)
        
        # Meta summary
        logger.info(
            "รวมรายการล่าสุด: {} | ระยะเวลาครอบคลุม: {} ~ {}".format(
                len(recent_defects_list),
                recent_defects_list[-1]['reportedDate'] if recent_defects_list else 'N/A',
                recent_defects_list[0]['reportedDate'] if recent_defects_list else 'N/A'
            )
        )

        # Flat per-record log in nice format with icons (like "table")
        if recent_defects_list:
            logger.info("รายการข้อบกพร่องล่าสุด:")
            for row in recent_defects_list:
                sevicon = SEVERITY_ICON.get(row['severity'], '•')
                sticon = STATUS_ICON.get(row['status'], '•')
                logger.info(
                    "  {} [{}] {} {} @ {} ({}) | {}".format(
                        sevicon, row['id'], row['severity'], sticon + row['status'] if sticon != '•' else row['status'],
                        row['module'], row['reportedDate'], row['description'][:60]
                    )
                )
        else:
            logger.info("ไม่มีรายการข้อบกพร่องที่จะแสดง (recent_defects_list ว่าง)")
            
        # Summary block at the end
        logger.info("✅ สรุป Recent Defects Data:")
        logger.info("  รายการล่าสุดทั้งหมด: {}".format(len(recent_defects_list)))
        severity_count = {}
        for row in recent_defects_list:
            severity_count[row['severity']] = severity_count.get(row['severity'], 0) + 1
        if severity_count:
            logger.info("  จำนวนแยกตาม Severity: {{{}}}".format(
                ", ".join("{} {}: {}".format(SEVERITY_ICON.get(sev, '•'), sev, cnt) for sev, cnt in severity_count.items())
            ))
        status_count = {}
        for row in recent_defects_list:
            status_count[row['status']] = status_count.get(row['status'], 0) + 1
        if status_count:
            logger.info("  จำนวนแยกตาม Status: {{{}}}".format(
                ", ".join("{} {}: {}".format(STATUS_ICON.get(st, '•'), st, cnt) for st, cnt in status_count.items())
            ))

        logger.info("✅ เสร็จสิ้นการเตรียม Recent Defects Data")
        return {"recent_defects": recent_defects_list}
    except Exception as e:
        logger.error("❌ เกิดข้อผิดพลาดในการเตรียม Recent Defects Data: {}".format(str(e)))
        return {"recent_defects": []}
