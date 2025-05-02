"""
Module Testing Prepare Module
รับผิดชอบการเตรียมข้อมูลสถานะการทดสอบแยกตามโมดูล

Author: Tassana Khrueawan
Version: 1.0.0
"""

from typing import Dict, Any, List
from robot.api import logger
import os
import sys
from collections import defaultdict

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger

logger = get_logger("ModuleTestingPrepare")

def prepare_module_testing_status_data(test_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    เตรียมข้อมูล Module Testing Status โดยเฉพาะ
    - แสดงสถานะการทดสอบแยกตามโมดูล
    - คำนวณอัตราส่วนความสำเร็จและความล้มเหลว
    - จัดเรียงผลลัพธ์ตามจำนวน test case

    Args:
        test_data (Dict[str, Any]): ข้อมูลการทดสอบทั้งหมด

    Returns:
        Dict[str, Any]: Dictionary ที่มีข้อมูล Module Testing Status
    """
    logger.info('────────────────────────────────────────────────────────────────────')
    logger.info("🧩 [MODULE TEST] Module Testing Status Summary")
    
    modules_data = test_data.get('modules', [])
    module_results = []

    built_from_cases = False

    if not modules_data:
        logger.warning("⚠️ ไม่พบข้อมูล 'modules' ใน test data; จะพยายามสร้างจาก testCases ...")
        # Attempt to reconstruct modules data from testCases if available
        test_cases_list = test_data.get('testCases', [])
        if isinstance(test_cases_list, list) and test_cases_list:
            logger.info("🔄 กำลังสร้างข้อมูล module จาก testCases ...")
            
            # กำหนดโครงสร้างข้อมูลเริ่มต้นสำหรับแต่ละโมดูล
            modules_temp = defaultdict(lambda: {
                "total": 0, "passed": 0, "failed": 0, 
                "blocked": 0, "inProgress": 0, "notStarted": 0
            })
            
            # กำหนดการแปลงสถานะให้เป็นมาตรฐาน
            KNOWN_STATUSES = {
                "pass": "passed",
                "fail": "failed",
                "block": "blocked",
                "blocked": "blocked",
                "inprogress": "inProgress",
                "in progress": "inProgress",
                "notstarted": "notStarted",
                "not started": "notStarted"
            }

            for tc in test_cases_list:
                module_name = tc.get('module') or tc.get('component') or "Unknown"
                status_raw = str(tc.get('status', '')).lower().strip()
                status = KNOWN_STATUSES.get(status_raw, "notStarted")
                modules_temp[module_name]['total'] += 1
                modules_temp[module_name][status] += 1

            for name, counts in modules_temp.items():
                modules_data.append({"name": name, "testCases": dict(counts)})
            
            logger.info(f"✅ สร้างข้อมูล module สำเร็จ {len(modules_data)} modules")
            built_from_cases = True
        else:
            logger.warning("❌ ไม่มีข้อมูล testCases หรือไม่สามารถสร้าง modules ได้จาก testCases")
            logger.info('────────────────────────────────────────────────────────────────────')
            return {"module_testing_status": []}

    total_testcase = 0
    total_passed = 0
    total_failed = 0
    total_blocked = 0
    total_in_progress = 0
    total_not_started = 0

    # ประมวลผลข้อมูลแต่ละโมดูล
    for module in modules_data:
        name = module.get('name', 'Unknown Module')
        cases = module.get('testCases', {})
        
        # แปลงค่าเป็น int เพื่อป้องกันปัญหาการคำนวณ
        total = int(cases.get('total', 0))
        passed = int(cases.get('passed', 0))
        failed = int(cases.get('failed', 0))
        blocked = int(cases.get('blocked', cases.get('block', 0)))
        in_progress = int(cases.get('inProgress', 0))
        
        not_started = int(cases.get('notStarted', total - passed - failed - blocked - in_progress))
        if total <= 0:
            logger.warning(f"⚠️ โมดูล '{name}' มีจำนวน test case ทั้งหมดเป็น 0 หรือติดลบ")
            total = max(1, passed + failed + blocked + in_progress + not_started)
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        fail_rate = (failed / total) * 100 if total > 0 else 0
        
        total_testcase += total
        total_passed += passed
        total_failed += failed
        total_blocked += blocked
        total_in_progress += in_progress
        total_not_started += not_started

        module_results.append({
            'MODULE_NAME': name,
            'TOTAL': total,
            'PASSED': passed,
            'FAILED': failed,
            'BLOCKED': blocked,
            'IN_PROGRESS': in_progress,
            'NOT_STARTED': not_started,
            'PASS_RATE': round(pass_rate, 1),
            'FAIL_RATE': round(fail_rate, 1)
        })

    # เรียงตามจำนวน test case มากไปน้อย
    module_results.sort(key=lambda x: x['TOTAL'], reverse=True)

    module_count = len(module_results)
    # BLOCK: LOG MODULE SUMMARY ARRAY
    logger.info(f"MODULE_TESTING_STATUS_DATA: {module_results}")

    # BLOCK: LOG FLAT SUMMARY
    logger.info("✅ สรุป Module Testing Status:")
    logger.info(f"  TOTAL_MODULES: {module_count}")
    logger.info(f"  TOTAL_TESTCASES: {total_testcase}")
    logger.info(f"  TOTAL_PASSED: {total_passed}")
    logger.info(f"  TOTAL_FAILED: {total_failed}")
    logger.info(f"  TOTAL_BLOCKED: {total_blocked}")
    logger.info(f"  TOTAL_IN_PROGRESS: {total_in_progress}")
    logger.info(f"  TOTAL_NOT_STARTED: {total_not_started}")

    logger.info(f"✅ เตรียมข้อมูล Module Testing Status เสร็จสมบูรณ์ ({module_count} modules)")
    logger.info('────────────────────────────────────────────────────────────────────')
    return {
        "module_testing_status": module_results,
        "TOTAL_MODULES": module_count,
        "TOTAL_TESTCASES": total_testcase,
        "TOTAL_PASSED": total_passed,
        "TOTAL_FAILED": total_failed,
        "TOTAL_BLOCKED": total_blocked,
        "TOTAL_IN_PROGRESS": total_in_progress,
        "TOTAL_NOT_STARTED": total_not_started,
    }
