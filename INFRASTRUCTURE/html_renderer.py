"""
HTML Renderer
Responsible for rendering HTML reports from templates
"""

import os
import jinja2
from typing import Dict, Any, Optional
from datetime import datetime

from UTILS import get_logger, cache, TemplateUtils

# Setup logger
logger = get_logger("HTMLRenderer")

class HTMLRenderer:
    """
    Renders HTML reports using Jinja2 templates
    """
    
    def __init__(self):
        """Initialize HTML renderer"""
        self.template_env = None
        self.template_utils = TemplateUtils()
        
    def _setup_environment(self, template_dir: str) -> None:
        """
        Setup Jinja2 environment with template directory
        
        Args:
            template_dir (str): Directory containing templates
        """
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.template_env.filters.update({
            'format_datetime': self.template_utils.format_datetime,
            'format_date': self.template_utils.format_date,
            'as_percent': self.template_utils.as_percent,
            'format_number': self.template_utils.format_number,
            'to_datetime': self.template_utils.to_datetime,
            'safe_json': self.template_utils.safe_json_loads,
            'ensure_dict': self.template_utils.ensure_dict,
            'default_dict': self.template_utils.default_dict
        })

    @cache(300)  # Cache for 5 minutes
    def render(self, report_data: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """
        Render and save HTML report
        
        Args:
            report_data (Dict[str, Any]): Processed report data
            output_dir (Optional[str]): Directory to save report
        
        Returns:
            str: Path of the generated report
        """
        template_path = report_data.get("TEMPLATE_PATH", "templates/base.html")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)

        self._setup_environment(template_dir)

        template = self.template_env.get_template(template_file)

        html_content = template.render(**report_data)

        # Save output
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "qa_reports")
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"qa_report_{self._timestamp()}.html")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"QA Report generated at: {output_file}")
        return output_file

    def _timestamp(self) -> str:
        """
        Generate timestamp string
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S") 