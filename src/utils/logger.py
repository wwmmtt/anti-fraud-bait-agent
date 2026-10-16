"""loguru 日志配置"""
import sys
from pathlib import Path
from loguru import logger

from config.settings import PROJECT_ROOT

logger.remove()
logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | {level} | {message}")
# 日志文件锚定项目根 logs/，从任何目录启动都写同一处
logger.add(str(PROJECT_ROOT / "logs" / "bait.log"), rotation="10 MB", retention="7 days", level="DEBUG")
