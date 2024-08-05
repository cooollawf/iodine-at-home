import sys
from core.logger import logger

py_version = sys.version_info

if py_version < (3, 9):
    logger.info(f'你使用的 Python 版本是 {py_version[0]}.{py_version[1]}.{py_version[2]}，')
    logger.info(f'而该程序要求使用 3.9 版本及以上的 Python，请及时更换。')
    sys.exit(1)
import core
core.init() # 初始化