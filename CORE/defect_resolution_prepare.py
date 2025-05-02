
"""
Defect Resolution Prepare Module
รับผิดชอบการเตรียมข้อมูลเวลาที่ใช้ในการแก้ไขข้อบกพร่อง

Author: Tassana Khrueawan
Version: 1.0.2 (Logging Style Update FIXED)
"""

from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime
from robot.api import logger
import os
import sys

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger
from CORE.defect_analyzer import calculate_resolution_days # Import ฟังก์ชันคำนวณ

logger = get_logger("DefectResolutionPrepare")

def prepare_defect_resolution_time_data(defects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    เตรียมข้อมูล Defect Resolution Time โดยเฉพาะ
    - วิเคราะห์เวลาที่ใช้ในการแก้ไขข้อบกพร่องตาม Severity

    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด

    Returns:
        Dict[str, Any]: Dictionary ที่มีข้อมูล Defect Resolution Time
    """
    try:
        ICONS = {
            'Critical': '🔥', 'Major': '⚠️', 'Moderate': '🔶', 
            'Minor': '🔹', 'Trivial': '⬇️', 'Unknown': '❓',
        }

        logger.info("—— ผลรวม Defect Resolution Time Analysis ——")

        if not defects_data:
            logger.warning("⚠️ ไม่มีข้อมูล defects สำหรับ Defect Resolution Time")
            logger.info("✅ เตรียมข้อมูล Defect Resolution Time เรียบร้อยแล้ว (ข้อมูลว่าง)")
            return {
                "resolution_time_by_severity": {},
                "average_resolution_time_overall": 0,
                "details": []
            }

        resolution_times_by_severity = defaultdict(list)
        all_resolution_times = []
        details = []

        for defect in defects_data:
            if defect.get('status', '').lower() in ['closed', 'fixed', 'resolved', 'completed', 'done']:
                reported_date = defect.get('reportedDate', defect.get('created_date', ''))
                closed_date = defect.get('closedDate', defect.get('closed_date', ''))
                severity = str(defect.get('severity', 'Unknown')).capitalize()
                key_sev = severity if severity in ICONS else 'Unknown'

                if reported_date and closed_date:
                    days = calculate_resolution_days(reported_date, closed_date)
                    if days is not None:
                        resolution_times_by_severity[key_sev].append(days)
                        all_resolution_times.append(days)
                        details.append({
                            "id": defect.get("id", "-"),
                            "title": defect.get("title", defect.get("summary", "")),
                            "severity": key_sev,
                            "status": defect.get("status", ""),
                            "resolution_days": days,
                        })

        avg_resolution_by_severity = {}
        for severity, times in resolution_times_by_severity.items():
            if times:
                avg_resolution_by_severity[severity] = round(float(sum(times)) / len(times), 2)

        avg_resolution_overall = round(float(sum(all_resolution_times)) / len(all_resolution_times), 2) if all_resolution_times else 0

        total_closed = len(all_resolution_times)
        total_defects = len(defects_data)
        closed_percent = (float(total_closed) / total_defects) * 100 if total_defects else 0.0

        logger.info("รวม {} | ✅ ปิดแล้ว {} ({:.1f}%) | ⏱️ เฉลี่ยการแก้ไข: {:.2f} วัน".format(
            total_defects, total_closed, closed_percent, avg_resolution_overall
        ))

        if avg_resolution_by_severity:
            items = ["{} {}: {:.2f} วัน".format(ICONS.get(sev, '•'), sev, days) for sev, days in avg_resolution_by_severity.items()]
            logger.info("รายละเอียดเวลาแก้ไขเฉลี่ย (แบ่งตามความรุนแรง): {}".format(" | ".join(items)))
        else:
            logger.info("ไม่พบข้อมูลเวลาเฉลี่ยแยกตาม Severity")

        if avg_resolution_by_severity:
            max_sev = max(avg_resolution_by_severity.items(), key=lambda x: x[1])
            logger.info("ความรุนแรงที่ใช้เวลาแก้ไขเฉลี่ยสูงสุด: {} {} ({:.2f} วัน)".format(
                ICONS.get(max_sev[0], '•'), max_sev[0], max_sev[1]
            ))

        # Flat summary
        logger.info("✅ สรุป Defect Resolution Time Data:")
        logger.info("  RESOLUTION_TIME_BY_SEVERITY: {{{}}}".format(
            ", ".join("{} {}: {:.2f}".format(ICONS.get(sev, '•'), sev, v) for sev, v in avg_resolution_by_severity.items())
        ))
        logger.info("  AVERAGE_RESOLUTION_TIME_OVERALL: {:.2f}".format(avg_resolution_overall))
        logger.info("  TOTAL_DEFECTS: {}".format(total_defects))
        logger.info("  TOTAL_CLOSED: {}".format(total_closed))
        logger.info("  CLOSED_PERCENT: {:.1f}".format(closed_percent))

        logger.info("✅ เสร็จสิ้นการเตรียม Defect Resolution Time Data")
        return {
            "resolution_time_by_severity": avg_resolution_by_severity,
            "average_resolution_time_overall": avg_resolution_overall,
            "details": details
        }
    except Exception as e:
        logger.error("❌ เกิดข้อผิดพลาดในการเตรียม Defect Resolution Time Data: {}".format(str(e)))
        return {
            "resolution_time_by_severity": {},
            "average_resolution_time_overall": 0,
            "details": []
        }
