"""
Configuration Module
Contains configuration settings for QAReportLibrary

"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class ReportConfig:
    """
    Configuration class for QA Report
    """
    # Default configuration values
    ROBOT_LIBRARY_SCOPE: str = 'GLOBAL'
    
    # File paths
    project_root: Optional[str] = None
    template_name: Optional[str] = None
    data_file: Optional[str] = None
    defects_file: Optional[str] = None
    output_dir: Optional[str] = None
    
    # SLA configuration for different severity levels (days)
    sla_limits: Dict[str, int] = field(default_factory=lambda: {
        "Critical": 3,  # 3 days for Critical
        "High": 5,      # 5 days for High
        "Medium": 7,    # 7 days for Medium
        "Low": 14       # 14 days for Low
    })
    
    # Cache configuration
    enable_caching: bool = True
    cache_duration: int = 3600  # 1 hour in seconds
    
    # Logging configuration
    log_level: str = 'INFO'
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __post_init__(self) -> None:
        """Initialize derived values after instance creation"""
        if self.log_to_file and not self.log_file_path:
            # Default log file path if not specified
            import os
            if self.project_root:
                self.log_file_path = os.path.join(self.project_root, 'qa_report.log')
            else:
                self.log_file_path = 'qa_report.log'

# Global configuration instance
config = ReportConfig() 