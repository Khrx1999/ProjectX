#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TemplateFinder - เครื่องมือค้นหาและวิเคราะห์ตัวแปรใน HTML Template

ใช้สำหรับค้นหาตัวแปรที่ใช้ใน HTML Template และแสดงข้อมูลเกี่ยวกับตัวแปรเหล่านั้น 
รวมถึงการจัดกลุ่มและแสดงคำอธิบายภาษาไทย

Author: QA Automation Team
"""

import re
import os
import time
import logging
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Any, Union

# สร้าง logger
def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class TemplateFinder:
    """คลาสสำหรับค้นหาและวิเคราะห์ตัวแปรใน HTML Template"""
    
    def __init__(self):
        """กำหนดค่าเริ่มต้นสำหรับคลาส TemplateFinder"""
        self.key_descriptions = {
            # ตัวแปรข้อมูลการทดสอบ
            'PASSED_TEST_CASES': 'จำนวนเคสที่ผ่าน',
            'FAILED_TEST_CASES': 'จำนวนเคสที่ไม่ผ่าน',
            'BLOCKED_TEST_CASES': 'จำนวนเคสที่ถูกบล็อก',
            'IN_PROGRESS_TEST_CASES': 'จำนวนเคสที่กำลังดำเนินการ',
            'NOT_STARTED_TEST_CASES': 'จำนวนเคสที่ยังไม่ได้เริ่ม',
            'TOTAL_TEST_CASES': 'จำนวนเคสทั้งหมด',
            'TEST_COVERAGE': 'เปอร์เซ็นต์ความครอบคลุมการทดสอบ',
            'COVERAGE_GROWTH': 'การเติบโตของความครอบคลุม',
            'EXECUTED_CASES': 'จำนวนเคสที่ถูกนำไปทดสอบแล้ว',
            
            # ตัวแปรความคืบหน้าของสปรินท์
            'COMPLETION_PROGRESS': 'เปอร์เซ็นต์ความสำเร็จโดยรวม',
            'REMAINING_PROGRESS': 'เปอร์เซ็นต์ที่เหลือ',
            'EXPECTED_PROGRESS': 'เปอร์เซ็นต์ที่คาดหวัง',
            'ACTUAL_PROGRESS_RATE': 'อัตราความคืบหน้าจริง',
            'PROGRESS_STATUS': 'สถานะความคืบหน้า',
            'PROGRESS_STATUS_COLOR': 'สีที่แสดงสถานะ',
            'PROGRESS_PER_DAY': 'เปอร์เซ็นต์เป้าหมายต่อวัน',
            'necessary_velocity': 'ความเร็วที่จำเป็นในการทำงานให้เสร็จตามกำหนด',
            
            # ตัวแปรด้านเวลา
            'DAYS_PASSED': 'จำนวนวันที่ผ่านไป',
            'DAYS_REMAINING': 'จำนวนวันที่เหลือ',
            'TOTAL_DAYS': 'จำนวนวันทั้งหมด',
            'START_DATE': 'วันที่เริ่มต้น',
            'END_DATE': 'วันที่สิ้นสุด',
            'DAYS_TO_COMPLETION': 'จำนวนวันที่ต้องใช้จนเสร็จ',
            'DAYS_DIFFERENCE': 'ความแตกต่างของวัน',
            
            # ตัวแปรด้านข้อบกพร่อง
            'DEFECT_DENSITY': 'ความหนาแน่นของข้อบกพร่องต่อโค้ด 1000 บรรทัด',
            'DEFECT_FIX_RATE': 'อัตราการแก้ไขข้อบกพร่อง (เปอร์เซ็นต์)',
            'FIXED_DEFECTS': 'จำนวนข้อบกพร่องที่แก้ไขแล้ว',
            'OPEN_DEFECTS': 'จำนวนข้อบกพร่องที่ยังเปิดค้างอยู่',
            'TOTAL_DEFECTS': 'จำนวนข้อบกพร่องทั้งหมด',
            'AVG_FIX_TIME': 'เวลาเฉลี่ยในการแก้ไขข้อบกพร่อง (วัน)',
            'FIX_TIME_CHANGE': 'การเปลี่ยนแปลงของเวลาในการแก้ไข (เปอร์เซ็นต์)',
            'TOTAL': 'จำนวนรวมทั้งหมด',
            
            # ตัวแปรสัดส่วนข้อบกพร่อง
            'critical_percent': 'เปอร์เซ็นต์ข้อบกพร่องระดับวิกฤติ',
            'high_percent': 'เปอร์เซ็นต์ข้อบกพร่องระดับสูง',
            'medium_percent': 'เปอร์เซ็นต์ข้อบกพร่องระดับกลาง',
            'low_percent': 'เปอร์เซ็นต์ข้อบกพร่องระดับต่ำ',
            
            # ตัวแปรการทดสอบเพิ่มเติม
            'block_percent': 'เปอร์เซ็นต์ของเคสที่ถูกบล็อก',
            'fail_percent': 'เปอร์เซ็นต์ของเคสที่ไม่ผ่าน',
            'other_percent': 'เปอร์เซ็นต์ของเคสประเภทอื่นๆ',
            
            # ไฟล์ย่อย (Partials)
            'summary_overall_progress.html': 'แสดงความคืบหน้าโดยรวมของสปรินท์',
            'summary_test_coverage.html': 'แสดงข้อมูลความครอบคลุมการทดสอบ',
            'summary_defect_density.html': 'แสดงข้อมูลความหนาแน่นของข้อบกพร่อง',
            'summary_time_to_fix.html': 'แสดงเวลาที่ใช้ในการแก้ไขข้อบกพร่อง',
            'defect_recent_defects.html': 'แสดงข้อบกพร่องล่าสุด'
        }
        
        # นิยามกลุ่มของตัวแปร
        self.key_groups = {
            'การทดสอบ': [
                'PASSED_TEST_CASES', 'FAILED_TEST_CASES', 'BLOCKED_TEST_CASES', 
                'IN_PROGRESS_TEST_CASES', 'NOT_STARTED_TEST_CASES', 'TOTAL_TEST_CASES',
                'TEST_COVERAGE', 'COVERAGE_GROWTH', 'EXECUTED_CASES',
                'block_percent', 'fail_percent', 'other_percent'
            ],
            'ความคืบหน้า': [
                'COMPLETION_PROGRESS', 'REMAINING_PROGRESS', 'EXPECTED_PROGRESS', 
                'ACTUAL_PROGRESS_RATE', 'PROGRESS_STATUS', 'PROGRESS_STATUS_COLOR',
                'PROGRESS_PER_DAY', 'necessary_velocity'
            ],
            'เวลา': [
                'DAYS_PASSED', 'DAYS_REMAINING', 'TOTAL_DAYS', 'START_DATE', 
                'END_DATE', 'DAYS_TO_COMPLETION', 'DAYS_DIFFERENCE'
            ],
            'ข้อบกพร่อง': [
                'DEFECT_DENSITY', 'DEFECT_FIX_RATE', 'FIXED_DEFECTS', 'OPEN_DEFECTS',
                'TOTAL_DEFECTS', 'AVG_FIX_TIME', 'FIX_TIME_CHANGE', 'TOTAL',
                'critical_percent', 'high_percent', 'medium_percent', 'low_percent'
            ],
            'ไฟล์ย่อย': [
                'summary_overall_progress.html', 'summary_test_coverage.html',
                'summary_defect_density.html', 'summary_time_to_fix.html',
                'defect_recent_defects.html'
            ]
        }
        
        self.logger = get_logger("TemplateFinder")
    
    def find_template_keys(self, template_path: str, filter_keys: bool = False, with_description: bool = True) -> List[str]:
        """
        ค้นหาตัวแปรทั้งหมดที่ใช้ในไฟล์ template HTML
        
        Args:
            template_path (str): เส้นทางไฟล์ template HTML ที่ต้องการค้นหา keys
            filter_keys (bool, optional): กรองเฉพาะตัวแปรที่สำคัญที่มีคำอธิบาย
                                          ถ้าเป็น True จะแสดงเฉพาะตัวแปรที่มีการอธิบายไว้
            with_description (bool, optional): แสดงคำอธิบายของตัวแปรแต่ละตัว
                                            ถ้าเป็น True จะแสดงคำอธิบายของตัวแปรที่มีการอธิบายไว้
        
        Returns:
            List[str]: รายการตัวแปรทั้งหมดที่พบในไฟล์ template
            
        ตัวอย่างการใช้งาน:
            # ค้นหา keys ทั้งหมดในไฟล์ template
            finder = TemplateFinder()
            keys = finder.find_template_keys("path/to/template.html")
            
            # ค้นหาและแสดงเฉพาะตัวแปรที่สำคัญพร้อมคำอธิบาย
            keys = finder.find_template_keys("path/to/template.html", filter_keys=True)
        """
        logger = self.logger
        
        if not template_path:
            logger.error("❌ ไม่ได้ระบุ template_path")
            return []
        
        if not os.path.exists(template_path):
            logger.error(f"❌ ไม่พบไฟล์ template: {template_path}")
            return []
        
        logger.info(f"🔍 กำลังค้นหา keys ในไฟล์ template: {template_path}")
        start_time = time.time()
        
        try:
            # อ่านเนื้อหาไฟล์
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # สร้าง dictionary เก็บตัวแปรและตำแหน่งที่พบ
            variables_info = defaultdict(list)
            
            # 1. หา variables แบบ {{ variable }} หรือ {{variable}}
            variable_pattern = r'{{\s*([a-zA-Z_][\w.]*)\s*}}'
            for match in re.finditer(variable_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("มาตรฐาน", line_num))
            
            # 2. หา variables ใน if statements เช่น {% if variable %}, แยกเฉพาะชื่อตัวแปร
            if_pattern = r'{%\s*if\s+([a-zA-Z_][\w.]*)'
            for match in re.finditer(if_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("เงื่อนไข if", line_num))
            
            # 3. หา variables ใน for loops เช่น {% for item in items %}
            for_pattern = r'{%\s*for\s+\w+\s+in\s+([a-zA-Z_][\w.]*)'
            for match in re.finditer(for_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("วนซ้ำ for", line_num))
            
            # 4. หา variables ที่ใช้กับ filters เช่น {{ variable|filter }}
            filter_pattern = r'{{\s*([a-zA-Z_][\w.]*)\s*\|'
            for match in re.finditer(filter_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("filter", line_num))
            
            # 5. หา variables แบบ data-attr เช่น data-value="{{ variable }}"
            attr_pattern = r'data-\w+=["\']{{(\s*[a-zA-Z_][\w.]*\s*)}}'
            for match in re.finditer(attr_pattern, content):
                var_name = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("data-attribute", line_num))
            
            # 6. หา variables ใน get_specific_data
            specific_pattern = r'get_specific_data\([\'"]([^\'"]+)[\'"]\)'
            for match in re.finditer(specific_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("get_specific_data", line_num))
            
            # 7. หา variables ที่ใช้กับ operators เช่น {{ variable + 1 }} หรือ {{ variable == "value" }}
            operator_pattern = r'{{\s*([a-zA-Z_][\w.]*)\s*[\+\-\*\/\=\>\<]'
            for match in re.finditer(operator_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("operator", line_num))
            
            # 8. หา include statements
            include_pattern = r'{%\s*include\s+[\'"]partials/([^\'"]+)[\'"]\s*%}'
            for match in re.finditer(include_pattern, content):
                var_name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                variables_info[var_name].append(("include", line_num))
            
            # เก็บชื่อไฟล์ย่อยไว้เพื่อป้องกันการซ้ำซ้อน
            included_files = [key for key in variables_info.keys() if key.endswith('.html')]
            
            # แยกตัวแปรที่มีจุด (เช่น data.value) เป็นตัวแปรหลัก (data)
            base_variables = defaultdict(list)
            for key, locs in variables_info.items():
                # เพิ่มตัวแปรเต็มรูปแบบ
                base_variables[key] = locs
                
                # เพิ่มตัวแปรหลัก (ส่วนแรกก่อนจุด) - เฉพาะกรณีที่ไม่ใช่ชื่อไฟล์ที่ซ้ำซ้อน
                base_key = key.split('.')[0]
                if base_key != key:
                    # ตรวจสอบว่าเป็นตัวแปรที่จะซ้ำซ้อนกับชื่อไฟล์ย่อยหรือไม่
                    file_name = f"{base_key}.html"
                    if file_name not in included_files:
                        # บันทึกเป็นตัวแปรหลักที่มี nested attribute
                        for loc in locs:
                            base_variables[base_key].append((f"nested ({key})", loc[1]))
            
            # แปลงเป็น dict ปกติและเรียงตามตัวอักษร
            all_keys = sorted(base_variables.keys())
            
            # กรองเฉพาะตัวแปรที่สำคัญ (มีคำอธิบาย) ถ้า filter_keys เป็น True
            if filter_keys:
                filtered_keys = [key for key in all_keys if key in self.key_descriptions]
            else:
                filtered_keys = all_keys
            
            # สร้างข้อมูลผลลัพธ์
            elapsed_time = time.time() - start_time
            logger.info(f"✅ พบ keys ทั้งหมด {len(filtered_keys)} keys จาก {len(all_keys)} (ใช้เวลา {elapsed_time:.2f} วินาที)")
            logger.info(f"====================== TEMPLATE KEYS ======================")
            
            # จัดกลุ่มตัวแปร
            if with_description:
                # จัดกลุ่มตามประเภทที่กำหนด
                grouped_keys = {}
                ungrouped_keys = []
                
                for key in filtered_keys:
                    grouped = False
                    for group_name, keys_in_group in self.key_groups.items():
                        if key in keys_in_group:
                            if group_name not in grouped_keys:
                                grouped_keys[group_name] = []
                            grouped_keys[group_name].append(key)
                            grouped = True
                            break
                    
                    if not grouped:
                        ungrouped_keys.append(key)
                
                # แสดงตัวแปรตามกลุ่ม
                for group_name, keys in grouped_keys.items():
                    logger.info(f"\n🔹 ตัวแปรกลุ่ม{group_name} ({len(keys)} keys):")
                    for idx, key in enumerate(sorted(keys), 1):
                        # แสดงข้อมูลตัวแปร
                        desc = f" - {self.key_descriptions[key]}" if key in self.key_descriptions else ""
                        
                        # หาประเภทและตำแหน่งที่ไม่ซ้ำกัน
                        unique_locs = {}
                        for loc_type, line_num in base_variables[key]:
                            if loc_type not in unique_locs:
                                unique_locs[loc_type] = []
                            unique_locs[loc_type].append(line_num)
                        
                        # สร้าง string สำหรับแสดงผล
                        loc_info = []
                        for loc_type, lines in unique_locs.items():
                            # กรณีบรรทัดเยอะเกินไป แสดงแค่จำนวนรวม
                            if len(lines) > 3:
                                loc_info.append(f"{loc_type} ({len(lines)} แห่ง)")
                            else:
                                loc_info.append(f"{loc_type} (บรรทัด {', '.join(map(str, lines))})")
                        
                        loc_str = " | ".join(loc_info)
                        logger.info(f"  {idx}. {key}{desc} - {loc_str}")
                
                # แสดงตัวแปรที่ไม่ได้อยู่ในกลุ่มใด
                if ungrouped_keys:
                    logger.info(f"\n🔹 ตัวแปรทั่วไป ({len(ungrouped_keys)} keys):")
                    for idx, key in enumerate(sorted(ungrouped_keys), 1):
                        desc = f" - {self.key_descriptions[key]}" if key in self.key_descriptions else ""
                        
                        # หาประเภทและตำแหน่งที่ไม่ซ้ำกัน
                        unique_locs = {}
                        for loc_type, line_num in base_variables[key]:
                            if loc_type not in unique_locs:
                                unique_locs[loc_type] = []
                            unique_locs[loc_type].append(line_num)
                        
                        # สร้าง string สำหรับแสดงผล
                        loc_info = []
                        for loc_type, lines in unique_locs.items():
                            if len(lines) > 3:
                                loc_info.append(f"{loc_type} ({len(lines)} แห่ง)")
                            else:
                                loc_info.append(f"{loc_type} (บรรทัด {', '.join(map(str, lines))})")
                        
                        loc_str = " | ".join(loc_info)
                        logger.info(f"  {idx}. {key}{desc} - {loc_str}")
            else:
                # แยกตามประเภท (ตัวแปรปกติ, ตัวแปร nested)
                normal_keys = []
                nested_keys = []
                
                for key in filtered_keys:
                    if '.' in key:
                        nested_keys.append(key)
                    else:
                        normal_keys.append(key)
                
                # แสดงตัวแปรปกติ
                logger.info(f"\n🔹 ตัวแปรพื้นฐาน ({len(normal_keys)} keys):")
                for idx, key in enumerate(normal_keys, 1):
                    # หาประเภทและตำแหน่งที่ไม่ซ้ำกัน
                    unique_locs = {}
                    for loc_type, line_num in base_variables[key]:
                        if loc_type not in unique_locs:
                            unique_locs[loc_type] = []
                        unique_locs[loc_type].append(line_num)
                    
                    # สร้าง string สำหรับแสดงผล
                    loc_info = []
                    for loc_type, lines in unique_locs.items():
                        # กรณีบรรทัดเยอะเกินไป แสดงแค่จำนวนรวม
                        if len(lines) > 3:
                            loc_info.append(f"{loc_type} ({len(lines)} แห่ง)")
                        else:
                            loc_info.append(f"{loc_type} (บรรทัด {', '.join(map(str, lines))})")
                    
                    loc_str = " | ".join(loc_info)
                    logger.info(f"  {idx}. {key} - {loc_str}")
                
                # แสดงตัวแปร nested
                if nested_keys:
                    logger.info(f"\n🔹 ตัวแปร Nested ({len(nested_keys)} keys):")
                    for idx, key in enumerate(nested_keys, 1):
                        # หาประเภทและตำแหน่งที่ไม่ซ้ำกัน
                        unique_locs = {}
                        for loc_type, line_num in base_variables[key]:
                            if loc_type not in unique_locs:
                                unique_locs[loc_type] = []
                            unique_locs[loc_type].append(line_num)
                        
                        # สร้าง string สำหรับแสดงผล
                        loc_info = []
                        for loc_type, lines in unique_locs.items():
                            # กรณีบรรทัดเยอะเกินไป แสดงแค่จำนวนรวม
                            if len(lines) > 3:
                                loc_info.append(f"{loc_type} ({len(lines)} แห่ง)")
                            else:
                                loc_info.append(f"{loc_type} (บรรทัด {', '.join(map(str, lines))})")
                        
                        loc_str = " | ".join(loc_info)
                        parent_key = key.split('.')[0]
                        logger.info(f"  {idx}. {key} - {loc_str}")
            
            logger.info(f"==========================================================")
            
            return filtered_keys
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการค้นหา keys: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def check_key_exists(self, template_path: str, key_name: str) -> bool:
        """
        ตรวจสอบว่ามีตัวแปร (key) ชื่อที่ระบุอยู่ในไฟล์ template หรือไม่
        
        Args:
            template_path (str): เส้นทางไฟล์ template HTML ที่ต้องการตรวจสอบ
            key_name (str): ชื่อตัวแปรที่ต้องการตรวจสอบ
        
        Returns:
            bool: True หากพบตัวแปรในไฟล์ template, False หากไม่พบ
            
        ตัวอย่างการใช้งาน:
            finder = TemplateFinder()
            exists = finder.check_key_exists("path/to/template.html", "PROJECT_NAME")
        """
        keys = self.find_template_keys(template_path)
        logger = self.logger
        
        if key_name in keys:
            logger.info(f"✅ พบตัวแปร '{key_name}' ในไฟล์ template")
            return True
        else:
            logger.info(f"❌ ไม่พบตัวแปร '{key_name}' ในไฟล์ template")
            return False
    
    def add_key_description(self, key: str, description: str) -> None:
        """
        เพิ่มคำอธิบายสำหรับตัวแปรใหม่
        
        Args:
            key (str): ชื่อตัวแปรที่ต้องการเพิ่มคำอธิบาย
            description (str): คำอธิบายของตัวแปร
            
        ตัวอย่างการใช้งาน:
            finder = TemplateFinder()
            finder.add_key_description("NEW_METRIC", "ตัวชี้วัดใหม่ที่เพิ่มเข้ามา")
        """
        self.key_descriptions[key] = description
        
        # จัดกลุ่มตัวแปรใหม่ตามประเภท
        if key.startswith("TEST_") or key.endswith("_TEST_CASES"):
            self.key_groups['การทดสอบ'].append(key)
        elif key.endswith("_PROGRESS") or key.endswith("_RATE"):
            self.key_groups['ความคืบหน้า'].append(key)
        elif key.startswith("DAY") or key.endswith("_DATE") or "_DAY" in key:
            self.key_groups['เวลา'].append(key)
        elif key.endswith(".html"):
            self.key_groups['ไฟล์ย่อย'].append(key)
            
        self.logger.info(f"✅ เพิ่มคำอธิบายสำหรับตัวแปร '{key}' เรียบร้อยแล้ว")

# สำหรับทดสอบใช้งานตรงๆ
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
        filter_keys = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
        
        finder = TemplateFinder()
        finder.find_template_keys(template_path, filter_keys=filter_keys)
    else:
        print("Usage: python TemplateFinder.py <template_path> [filter_keys]")
        print("Example: python TemplateFinder.py TEMPLATES/partials/test_summary.html true") 