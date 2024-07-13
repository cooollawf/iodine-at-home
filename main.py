import sys
import time
print(time.time())
py_version = sys.version_info
if  py_version < (3, 9):
    print(f'你使用的 Python 版本是 {py_version[0]}.{py_version[1]}.{py_version[2]}，')
    print(f'而我们要求使用 3.9 版本以上的 Python，请及时更换。')
    sys.exit(1)
import core
core.init(py_version)