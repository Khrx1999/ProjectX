"""
Test Trend Prepare Module
รับผิดชอบการเตรียมข้อมูลแนวโน้มการทดสอบ พร้อมสรุป defect daily (open/close) จาก DEFECT.json

Author: Tassana Khrueawan
Version: 1.1.1 (Separate logs for daily defect and analysis summary)
"""

import json
from typing import Dict, Any, List
from robot.api import logger
import os
import sys
from collections import defaultdict

# เพิ่ม path เพื่อให้สามารถ import โมดูลอื่นๆ ได้
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from UTILS import get_logger

logger = get_logger("TestTrendPrepare")

def load_defects_from_file(defect_json_path="DATA/DEFECT.json"):
    """
    พยายามโหลด defect json ตาม path ที่ระบุ หรือใช้ path default (relative กับ root)
    """
    abspath = defect_json_path
    if not os.path.isabs(defect_json_path):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abspath = os.path.join(root, defect_json_path)
    if not os.path.exists(abspath):
        logger.warn(f"⚠️ ไม่พบไฟล์ DEFECT.json: {abspath}")
        return []
    try:
        with open(abspath, encoding="utf-8") as f:
            data = json.load(f)
        # รูปแบบ: {"defects": [ ... ]}
        return data.get("defects", []) if isinstance(data, dict) else data
    except Exception as e:
        logger.error(f"❌ โหลด DEFECT.json ผิดพลาด: {e}")
        return []

def prepare_test_trend_analysis_data(test_data: Dict[str, Any], defect_data: List[dict]=None, defect_json_path="DATA/DEFECT.json") -> Dict[str, Any]:
    logger.info('────────────────────────────────────────────────────────────────────')
    logger.info("[TEST TREND] Test Trend Analysis Summary")
    

    trend_analysis = test_data.get('TREND_ANALYSIS', {})
    

    if not trend_analysis or not isinstance(trend_analysis, dict):
         logger.warn("ไม่พบข้อมูล 'TREND_ANALYSIS' ที่ถูกต้องใน test data, สร้างข้อมูลเริ่มต้น")
         trend_analysis = {
             "DATA": [],
             "SUMMARY": {},
             "METRICS": {},
             "STATUS": {},
             "TOTALS": {},
             "INSIGHTS": {}
         }

    if 'SUMMARY' not in trend_analysis or not isinstance(trend_analysis['SUMMARY'], dict):
        trend_analysis['SUMMARY'] = {}
    
    if 'TOTALS' not in trend_analysis or not isinstance(trend_analysis['TOTALS'], dict):
        trend_analysis['TOTALS'] = {}
        
    if 'INSIGHTS' not in trend_analysis or not isinstance(trend_analysis['INSIGHTS'], dict):
        trend_analysis['INSIGHTS'] = {}
        
    trend_data_list = trend_analysis.get('DATA', [])
    trend_labels = json.dumps([item.get('DATE', '') for item in trend_data_list])
    trend_executed = json.dumps([item.get('TEST_CASES_EXECUTED', 0) for item in trend_data_list])
    trend_passed = json.dumps([item.get('TEST_CASES_PASSED', 0) for item in trend_data_list])
    trend_failed = json.dumps([item.get('TEST_CASES_FAILED', 0) for item in trend_data_list]) 
    trend_blocked = json.dumps([item.get('TEST_CASES_BLOCKED', 0) for item in trend_data_list])
    trend_in_progress = json.dumps([item.get('TEST_CASES_IN_PROGRESS', 0) for item in trend_data_list])
    trend_not_started = json.dumps([item.get('TEST_CASES_NOT_STARTED', 0) for item in trend_data_list])
    trend_coverage = json.dumps([item.get('TEST_COVERAGE', 0) for item in trend_data_list])

    if defect_data is None:
        defect_data = load_defects_from_file(defect_json_path)

    daily_open = defaultdict(int)
    daily_closed = defaultdict(int)
    for defect in defect_data:
        reported_date = defect.get("reportedDate")
        closed_date = defect.get("closedDate")
        if reported_date:
            daily_open[reported_date] += 1
        if closed_date:
            daily_closed[closed_date] += 1

    # summary ต่อวัน
    per_day_defects_summary = []
    for d in trend_data_list:
        date = d.get("DATE")
        open_cnt = daily_open.get(date, 0)
        close_cnt = daily_closed.get(date, 0)
        d["DEFECTS_OPENED"] = open_cnt
        d["DEFECTS_CLOSED"] = close_cnt
        per_day_defects_summary.append({
            "TEST_TREND_DATE": date,
            "TEST_TREND_EXECUTED": d.get("TEST_CASES_EXECUTED", 0),
            "TEST_TREND_PASSED": d.get("TEST_CASES_PASSED", 0),
            "TEST_TREND_FAILED": d.get("TEST_CASES_FAILED", 0),
            "TEST_TREND_BLOCKED": d.get("TEST_CASES_BLOCKED", 0),
            "TEST_TREND_IN_PROGRESS": d.get("TEST_CASES_IN_PROGRESS", 0),
            "TEST_TREND_NOT_STARTED": d.get("TEST_CASES_NOT_STARTED", 0),
            "DEFECT_TREND_OPENED": open_cnt,
            "DEFECT_TREND_CLOSED": close_cnt,
        })

    logger.info("—— ผลรวม Test Trend & Defect ในแต่ละวัน (JSON-style) ——")
    logger.info(f"TEST_TREND_DATA: {per_day_defects_summary}")
    
    total_days = len(trend_data_list)
    total_test_cases = sum(item.get('TEST_CASES_EXECUTED', 0) for item in trend_data_list)
    total_passed_cases = sum(item.get('TEST_CASES_PASSED', 0) for item in trend_data_list)
    total_failed_cases = sum(item.get('TEST_CASES_FAILED', 0) for item in trend_data_list)
    total_blocked_cases = sum(item.get('TEST_CASES_BLOCKED', 0) for item in trend_data_list)
    total_in_progress_cases = sum(item.get('TEST_CASES_IN_PROGRESS', 0) for item in trend_data_list)
    total_not_started_cases = sum(item.get('TEST_CASES_NOT_STARTED', 0) for item in trend_data_list)
    
    # หา pass rate
    pass_rate = 0.0
    if total_test_cases > 0:
        pass_rate = (total_passed_cases / total_test_cases) * 100
    
    # หา date range
    dates = [item.get('DATE') for item in trend_data_list if item.get('DATE')]
    first_date = min(dates) if dates else "-"
    last_date = max(dates) if dates else "-"
    
    # หาวันที่มีการ execute สูงสุด
    highest_executed = 0
    best_day = "-"
    for item in trend_data_list:
        if item.get('TEST_CASES_EXECUTED', 0) > highest_executed:
            best_day = item.get('DATE', "-")
            highest_executed = item.get('TEST_CASES_EXECUTED', 0)

    # ดึงข้อมูลเพิ่มเติมจาก trend_analysis
    totals = trend_analysis.get('TOTALS', {})
    latest_coverage = totals.get('LATEST_COVERAGE', 68)  # ค่า default หากไม่มีข้อมูล
    coverage_change = totals.get('COVERAGE_CHANGE', 0)
    defect_fix_rate = totals.get('DEFECT_FIX_RATE', 0)
    today_executed = totals.get('TODAY_EXECUTED', 0)
    today_opened = totals.get('TODAY_OPENED', 0)
    today_closed = totals.get('TODAY_CLOSED', 0)
    
    # ดึงข้อมูล insights
    insights = trend_analysis.get('INSIGHTS', {})
    top_defect_module = insights.get('TOP_DEFECT_MODULE', "-")
    top_defect_module_count = insights.get('TOP_DEFECT_MODULE_COUNT', 0)
    critical_defects = insights.get('CRITICAL_DEFECTS', 0)
    avg_fix_time = insights.get('AVG_FIX_TIME_IN_DAYS', 0)
    
    # ดึงข้อมูล metrics
    metrics = trend_analysis.get('METRICS', {})
    test_velocity_ratio = metrics.get('TEST_VELOCITY_RATIO', 0)
    defect_rate_ratio = metrics.get('DEFECT_RATE_RATIO', 0)
    time_to_fix_ratio = metrics.get('TIME_TO_FIX_RATIO', 0)
    coverage_growth_ratio = metrics.get('COVERAGE_GROWTH_RATIO', 0)
    
    # ดึงค่า summary
    summary = trend_analysis.get('SUMMARY', {})
    test_velocity = summary.get('TEST_VELOCITY', 0)
    defect_rate = summary.get('DEFECT_RATE', 0)
    coverage_growth = summary.get('COVERAGE_GROWTH', 0)

    # ปรับสี emoji ตามค่า
    pass_emoji = "🟢" if pass_rate >= 95 else ("🟡" if pass_rate >= 70 else "🔴")
    best_label = f"🔺 {best_day} (จำนวน {highest_executed} รายการ)" if best_day != "-" else "-"

    # ==== LOG SUMMARY ====
    logger.info("✅ สรุป Test Trend Analysis Data:")
    logger.info(f"  TREND_ANALYSIS_TOTAL_DAYS: {total_days}")
    logger.info(f"  TREND_ANALYSIS_TOTAL_TEST_CASES: {total_test_cases}")
    logger.info(f"  TREND_ANALYSIS_PASSED_TEST_CASES: {total_passed_cases}")
    logger.info(f"  TREND_ANALYSIS_FAILED_TEST_CASES: {total_failed_cases}")
    logger.info(f"  TREND_ANALYSIS_BLOCKED_TEST_CASES: {total_blocked_cases}")
    logger.info(f"  TREND_ANALYSIS_IN_PROGRESS_TEST_CASES: {total_in_progress_cases}")
    logger.info(f"  TREND_ANALYSIS_NOT_STARTED_TEST_CASES: {total_not_started_cases}")
    logger.info(f"  TREND_ANALYSIS_PASS_RATE: {pass_rate:.2f}")
    logger.info(f"  TREND_ANALYSIS_FIRST_TEST_DATE: {first_date}")
    logger.info(f"  TREND_ANALYSIS_LAST_TEST_DATE: {last_date}")
    logger.info(f"  TREND_ANALYSIS_HIGHEST_EXECUTED_DAY: {best_day}")
    logger.info(f"  TREND_ANALYSIS_HIGHEST_EXECUTION_COUNT: {highest_executed}")
    logger.info(f"  TREND_ANALYSIS_LATEST_COVERAGE: {latest_coverage}")
    logger.info(f"  TREND_ANALYSIS_COVERAGE_CHANGE: {coverage_change}")
    logger.info(f"  TREND_ANALYSIS_DEFECT_FIX_RATE: {defect_fix_rate}")
    logger.info(f"  TREND_ANALYSIS_TODAY_EXECUTED: {today_executed}")
    logger.info(f"  TREND_ANALYSIS_TODAY_OPENED: {today_opened}")
    logger.info(f"  TREND_ANALYSIS_TODAY_CLOSED: {today_closed}")
    
    # สร้าง dictionary สำหรับส่งกลับ
    result = {
        "TREND_ANALYSIS": trend_analysis, # เก็บ object ทั้งหมดไว้เพื่อใช้ในเทมเพลต
        "TEST_TREND_LABELS": trend_labels,
        "TEST_TREND_EXECUTED": trend_executed,
        "TEST_TREND_PASSED": trend_passed,
        "TEST_TREND_FAILED": trend_failed,
        "TEST_TREND_BLOCKED": trend_blocked,
        "TEST_TREND_IN_PROGRESS": trend_in_progress,
        "TEST_TREND_NOT_STARTED": trend_not_started,
        "TEST_TREND_COVERAGE": trend_coverage,
        "TEST_TREND_DATA": per_day_defects_summary,
        "TREND_ANALYSIS_TOTAL_DAYS": total_days,
        "TREND_ANALYSIS_TOTAL_TEST_CASES": total_test_cases,
        "TREND_ANALYSIS_PASSED_TEST_CASES": total_passed_cases,
        "TREND_ANALYSIS_FAILED_TEST_CASES": total_failed_cases,
        "TREND_ANALYSIS_BLOCKED_TEST_CASES": total_blocked_cases,
        "TREND_ANALYSIS_IN_PROGRESS_TEST_CASES": total_in_progress_cases,
        "TREND_ANALYSIS_NOT_STARTED_TEST_CASES": total_not_started_cases,
        "TREND_ANALYSIS_PASS_RATE": round(pass_rate, 2),
        "TREND_ANALYSIS_FIRST_TEST_DATE": first_date,
        "TREND_ANALYSIS_LAST_TEST_DATE": last_date,
        "TREND_ANALYSIS_HIGHEST_EXECUTED_DAY": best_day,
        "TREND_ANALYSIS_HIGHEST_EXECUTION_COUNT": highest_executed,
        "TREND_ANALYSIS_LATEST_COVERAGE": latest_coverage,
        "TREND_ANALYSIS_COVERAGE_CHANGE": coverage_change,
        "TREND_ANALYSIS_DEFECT_FIX_RATE": defect_fix_rate,
        "TREND_ANALYSIS_TODAY_EXECUTED": today_executed,
        "TREND_ANALYSIS_TODAY_OPENED": today_opened,
        "TREND_ANALYSIS_TODAY_CLOSED": today_closed,
        "TREND_ANALYSIS_TOP_DEFECT_MODULE": top_defect_module,
        "TREND_ANALYSIS_TOP_DEFECT_MODULE_COUNT": top_defect_module_count,
        "TREND_ANALYSIS_CRITICAL_DEFECTS": critical_defects,
        "TREND_ANALYSIS_AVG_FIX_TIME": avg_fix_time,
        "TREND_ANALYSIS_TEST_VELOCITY": test_velocity,
        "TREND_ANALYSIS_DEFECT_RATE": defect_rate,
        "TREND_ANALYSIS_COVERAGE_GROWTH": coverage_growth,
        "TREND_ANALYSIS_TEST_VELOCITY_RATIO": test_velocity_ratio,
        "TREND_ANALYSIS_DEFECT_RATE_RATIO": defect_rate_ratio,
        "TREND_ANALYSIS_TIME_TO_FIX_RATIO": time_to_fix_ratio,
        "TREND_ANALYSIS_COVERAGE_GROWTH_RATIO": coverage_growth_ratio,
        "TREND_ANALYSIS_TOTAL_DEFECTS_OPENED": totals.get('TOTAL_DEFECTS_OPENED', 0),
        "TREND_ANALYSIS_TOTAL_DEFECTS_CLOSED": totals.get('TOTAL_DEFECTS_CLOSED', 0)
    }
    
    logger.info("✅ เตรียมข้อมูล Test Trend Analysis เรียบร้อยแล้ว")
    logger.info('────────────────────────────────────────────────────────────────────')
    return result 
