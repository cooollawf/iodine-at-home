import os
from pathlib import Path

def scan_files(directory_path: Path, web_path: str | None = 'files'):
    """
    * 递归扫描目录及其子目录，返回该目录下所有文件的路径集合
    """
    files_list = []
    
    for dirpath, dirnames, filenames in os.walk(directory_path):

        unix_style_dirpath = dirpath.replace('\\', '/')
        web_dirpath = unix_style_dirpath.replace('files', web_path)
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
            filepath = f"{web_dirpath}/{filename}"
            files_list.append(filepath)
    
    return files_list

# 使用函数
all_file_paths = scan_files(Path('./files/'), 'download')

# 打印所有Unix风格的文件路径
for path in all_file_paths:
    print(path)