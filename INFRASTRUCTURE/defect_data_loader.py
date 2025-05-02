# INFRASTRUCTURE/defect_data_loader.py

"""
Defect Data Loader
Responsible for loading defect data JSON files
"""

import json
import os
from typing import Optional, Dict, Any, List

from UTILS import get_logger

# Setup logger
logger = get_logger("DefectDataLoader")

class DefectDataLoader:
    """
    Loader for Defect Data JSON Files
    """

    def load(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load and parse defect data JSON file
        
        Args:
            file_path (str): Path to defect data JSON file
        
        Returns:
            Optional[List[Dict[str, Any]]]: Parsed data or None if failed
        """
        if not os.path.exists(file_path):
            logger.error(f"Defect data file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Defect data loaded successfully from: {file_path}")
            
            # รองรับหลากหลายรูปแบบข้อมูล
            # 1. ถ้าเป็น list อยู่แล้ว ให้ใช้เลย
            if isinstance(data, list):
                return data
                
            # 2. ถ้าเป็น dict และมี key "defects" ให้ใช้ค่าของ key นี้
            if isinstance(data, dict):
                if "defects" in data and isinstance(data["defects"], list):
                    return data["defects"]
                    
                # 3. ถ้าไม่มี key "defects" แต่มี key อื่นๆ ที่เป็น list ให้เลือก key แรกที่เป็น list
                for key, value in data.items():
                    if isinstance(value, list) and value:
                        logger.info(f"Using '{key}' field as defects data")
                        return value
                        
                # 4. ถ้าไม่มี key ที่เป็น list ให้แปลงเป็น list แต่ละ item เป็น dict
                if data:
                    # แปลง dict เป็น list of dict items
                    defects_list = []
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # ถ้า value เป็น dict ก็เพิ่ม key เข้าไปในนั้น
                            value['id'] = key
                            defects_list.append(value)
                        else:
                            # ถ้า value ไม่ใช่ dict ก็สร้าง dict ใหม่
                            defects_list.append({'id': key, 'data': value})
                    if defects_list:
                        logger.info(f"Converted dictionary to list of {len(defects_list)} defects")
                        return defects_list
            
            # ถ้าไม่ตรงกับรูปแบบใดเลย ให้ warning และส่งค่า list ว่างกลับไป
            logger.warning(f"Defect data should be a list: {file_path}")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while loading defect data: {str(e)}")
            return None
