"""
Defect Distribution Prepare Module
รับผิดชอบการเตรียมข้อมูลการกระจายตัวของข้อบกพร่อง

Author: Tassana Khrueawan
Version: 1.0.0
"""

from typing import Dict, Any, List
from collections import defaultdict
from robot.api import logger
import os
import sys

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger

logger = get_logger("DefectDistributionPrepare")

def prepare_defect_distribution_data(defects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    เตรียมข้อมูล Defect Distribution โดยเฉพาะ
    - วิเคราะห์การกระจายตัวของข้อบกพร่องตาม Severity, Status, Module, Page

    Args:
        defects_data (List[Dict[str, Any]]): ข้อมูลข้อบกพร่องทั้งหมด

    Returns:
        Dict[str, Any]: ข้อมูล Defect Distribution สไตล์ block/summary/array
    """
    logger.info('────────────────────────────────────────────────────────────────────')
    logger.info("🔎 [DEFECT DISTRIBUTION] Defect Distribution Analysis Summary")

    # Default template data for empty
    default_data = {
        "BY_SEVERITY": [{"SEVERITY": "Unknown", "COUNT": 1}],
        "BY_STATUS": [{"STATUS": "Unknown", "COUNT": 1}],
        "BY_MODULE": [{"MODULE": "Unknown", "COUNT": 1}],
        "BY_PAGE": [{"PAGE": "Unknown", "COUNT": 1}]
    }
    
    if not defects_data:
        logger.warning("⚠️ ไม่มีข้อมูล defects สำหรับ Defect Distribution")
        logger.info("DEFECT_DISTRIBUTION_DATA: " + str(default_data))
        logger.info("✅ เตรียมข้อมูล Defect Distribution เรียบร้อยแล้ว (ข้อมูลว่าง)")
        logger.info('────────────────────────────────────────────────────────────────────')
        return default_data
        
    # Collect
    by_severity = defaultdict(int)
    by_status = defaultdict(int)
    by_module = defaultdict(int)
    by_page = defaultdict(int)
    
    for defect in defects_data:
        by_severity[defect.get('severity', 'Unknown').capitalize()] += 1
        by_status[defect.get('status', 'Unknown').capitalize()] += 1
        by_module[defect.get('module', 'Unknown')] += 1
        by_page[defect.get('page', 'Unknown')] += 1
        
    # convert to array of dict
    arr_by_severity = [{"SEVERITY": k, "COUNT": v} for k, v in sorted(by_severity.items(), key=lambda x: x[1], reverse=True)]
    arr_by_status = [{"STATUS": k, "COUNT": v} for k, v in sorted(by_status.items(), key=lambda x: x[1], reverse=True)]
    arr_by_module = [{"MODULE": k, "COUNT": v} for k, v in sorted(by_module.items(), key=lambda x: x[1], reverse=True)]
    arr_by_page = [{"PAGE": k, "COUNT": v} for k, v in sorted(by_page.items(), key=lambda x: x[1], reverse=True)]
    
    # สร้าง sorted lists สำหรับใช้ใน template โดยตรง (เก็บไว้เพื่อความเข้ากันได้กับโค้ดเดิม)
    sorted_modules = [[item["MODULE"], item["COUNT"]] for item in arr_by_module]
    sorted_pages = [[item["PAGE"], item["COUNT"]] for item in arr_by_page]
    
    # ตรวจสอบว่ามีข้อมูลหรือไม่ ถ้าไม่มีให้ใส่ข้อมูลเริ่มต้น
    if not arr_by_module:
        arr_by_module = [{"MODULE": "Unknown", "COUNT": 1}]
        sorted_modules = [["Unknown", 1]]
    
    if not arr_by_page:
        arr_by_page = [{"PAGE": "Unknown", "COUNT": 1}]
        sorted_pages = [["Unknown", 1]]
    
    # Log summary
    logger.info("—— ผลรวม Defect Distribution ——")
    logger.info(" BY_SEVERITY: " + " | ".join([f"{x['SEVERITY']}: {x['COUNT']}" for x in arr_by_severity[:5]]))
    logger.info(" BY_STATUS: " + " | ".join([f"{x['STATUS']}: {x['COUNT']}" for x in arr_by_status[:5]]))
    logger.info(" BY_MODULE: " + " | ".join([f"{x['MODULE']}: {x['COUNT']}" for x in arr_by_module[:5]]))
    logger.info(" BY_PAGE:   " + " | ".join([f"{x['PAGE']}: {x['COUNT']}" for x in arr_by_page[:5]]))
    
    # Output main group as json-style array
    distribution_data = {
        "BY_SEVERITY": arr_by_severity,
        "BY_STATUS": arr_by_status,
        "BY_MODULE": arr_by_module,
        "BY_PAGE": arr_by_page,
        "TOTAL_DEFECTS": len(defects_data),
        "MODULE_COUNT": len(arr_by_module),
        "PAGE_COUNT": len(arr_by_page)
    }
    
    logger.info(f"DEFECT_DISTRIBUTION_DATA: " + str(distribution_data))
    
    # flat summary log
    logger.info("✅ สรุป Defect Distribution Data:")
    logger.info(f"  TOTAL_DEFECTS: {len(defects_data)}")
    logger.info(f"  MODULE_COUNT: {len(arr_by_module)}")
    logger.info(f"  PAGE_COUNT: {len(arr_by_page)}")
    logger.info("✅ เตรียมข้อมูล Defect Distribution เรียบร้อยแล้ว")
    logger.info('────────────────────────────────────────────────────────────────────')
    
    # สร้างผลลัพธ์ที่เข้ากันได้กับโค้ดเดิม
    result = {
        "distribution_by_severity": {item["SEVERITY"]: item["COUNT"] for item in arr_by_severity},
        "distribution_by_status": {item["STATUS"]: item["COUNT"] for item in arr_by_status},
        "distribution_by_module": {item["MODULE"]: item["COUNT"] for item in arr_by_module},
        "distribution_by_page": {item["PAGE"]: item["COUNT"] for item in arr_by_page},
        "sorted_modules": sorted_modules,
        "sorted_pages": sorted_pages,
        # เพิ่มข้อมูลใหม่ในรูปแบบ array
        "BY_SEVERITY": arr_by_severity,
        "BY_STATUS": arr_by_status,
        "BY_MODULE": arr_by_module,
        "BY_PAGE": arr_by_page,
        "TOTAL_DEFECTS": len(defects_data),
        "MODULE_COUNT": len(arr_by_module),
        "PAGE_COUNT": len(arr_by_page)
    }
    
    return result
