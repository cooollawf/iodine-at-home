import traceback

def format_exception(e):
    # 获取异常的详细信息
    exc_type, exc_value, exc_tb = type(e), e, e.__traceback__
    
    # 格式化异常的追踪信息
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    
    # 输出追踪信息
    formatted_traceback = ''.join(tb_lines)
    print(formatted_traceback)

while 1:
    command = input(">>> ")
    if command.strip().endswith('\\'):
        while command.strip().endswith('\\'):
            command += command.strip()[:-1]
            command += '\n'
            command += input("... ")
    try:
        exec(command)
    except Exception as e:
        print(format_exception(e))