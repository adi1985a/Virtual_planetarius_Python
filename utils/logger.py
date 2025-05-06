import logging
import os
from datetime import datetime

def setup_logger():
    """Configure and return a logger instance."""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f'planetarium_{datetime.now().strftime("%Y%m%d")}.log')
    
    logger = logging.getLogger('PlanetariumLogger')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
