import logging
from datetime import datetime
from typing import Dict, Any
import json

class ActivityLogger:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('activity_monitor')
        
    def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """
        记录活动日志
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'details': details
        }
        self.logger.info(json.dumps(log_entry)) 