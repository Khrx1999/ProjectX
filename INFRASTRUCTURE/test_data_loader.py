# INFRASTRUCTURE/test_data_loader.py

"""
Test Data Loader
Responsible for loading test result JSON data
"""

import json
import os
from typing import Optional, Dict, Any

from UTILS import get_logger

# Setup logger
logger = get_logger("TestDataLoader")

class TestDataLoader:
    """
    Loader for Test Result JSON Data
    """

    def load(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and parse test result JSON file
        
        Args:
            file_path (str): Path to test result JSON file
        
        Returns:
            Optional[Dict[str, Any]]: Parsed data or None if failed
        """
        if not os.path.exists(file_path):
            logger.error(f"Test data file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Test data loaded successfully from: {file_path}")

            # (Optional) Validate required fields
            if "dashboard" not in data or "testCases" not in data:
                logger.warning(f"Test data missing essential fields: {file_path}")
                return None

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while loading test data: {str(e)}")
            return None
