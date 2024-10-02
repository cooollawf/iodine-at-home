import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QPlainTextEdit, QLineEdit, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QProcess

class TerminalWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 创建一个垂直布局
        layout = QVBoxLayout(self)

        # 创建文本框用于显示命令的输出
        self.output_display = QPlainTextEdit(self)
        self.output_display.setReadOnly(True)  # 设置为只读
        self.output_display.setFixedHeight(150)  # 限制输出框高度
        layout.addWidget(self.output_display)

        # 创建一个水平布局用于放置负载标签
        load_layout = QHBoxLayout()
        
        # 创建显示当前负载的标签
        self.load_label = QLabel("当前负载：test", self)
        load_layout.addWidget(self.load_label)  # 将负载标签添加到布局中
        
        layout.addLayout(load_layout)  # 将负载标签的布局添加到主布局
        
        # 创建一个垂直布局用于放置输入框和按钮
        v_layout = QVBoxLayout()
        
        # 创建输入框并设置样式
        self.input_line = QLineEdit(self)
        self.input_line.setStyleSheet("border: 2px solid black; border-radius: 10px; padding: 8px;")  # 设置黑色边框和圆角
        v_layout.addWidget(self.input_line)

        # 创建执行命令按钮
        btn_execute = QPushButton("执行 python iodine.py", self)
        btn_execute.setFixedSize(200, 40)  # 设置按钮大小
        btn_execute.clicked.connect(self.run_command)
        v_layout.addWidget(btn_execute)

        layout.addLayout(v_layout)  # 将输入框和按钮的布局添加到主布局

        self.setLayout(layout)  # 设置主布局

        self.process = None  # 初始化进程为 None

        # 连接输入框的回车事件
        self.input_line.returnPressed.connect(self.run_command)

    def run_command(self):
        """执行命令并显示输出"""
        command = "python"
        args = [r"main.py"]  # 请替换为您的实际路径

        # 确保之前的进程结束
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()  # 结束之前的进程

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)  # 合并输出和错误输出
        self.process.readyReadStandardOutput.connect(self.update_output)  # 连接输出信号
        self.process.readyReadStandardError.connect(self.update_output)  # 连接错误输出信号

        try:
            print(f"Starting command: {command} with args: {args}")  # 调试信息
            self.process.start(command, args)  # 执行命令
            if not self.process.waitForStarted():  # 检查进程是否成功启动
                QMessageBox.critical(self, "错误", "进程启动失败，请检查是否正确设置了 python 路径和 iodine.py 文件路径。")
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"运行命令时发生错误: {str(e)}")

    def update_output(self):
        """更新输出显示并更新负载信息"""
        output = self.process.readAll().data().decode()  # 读取输出
        self.output_display.appendPlainText(output)  # 显示命令输出

        # 检查输出的内容并处理
        for line in output.splitlines():
            if line.startswith("overload:"):  # 如果行以 "overload:" 开头
                overload_info = line.split(":", 1)  # 提取冒号后的部分
                if len(overload_info) > 1:
                    overload_message = overload_info[1].strip()  # 去掉空格
                    self.load_label.setText("当前负载：" + overload_message)  # 更新负载标签显示

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)  # 去掉原生标题栏
        self.setGeometry(100, 100, 800, 350)  # 窗口初始位置和大小
        self.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF; font-family: 'Microsoft YaHei';")  # 设置背景为深灰色，字体为白色

        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建自定义标题栏
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标题字样
        title_label = QLabel("iodine-at-home", self)
        title_label.setStyleSheet("font-size: 20px; color: #FFFFFF;")  # 设置标题字体颜色为白色
        title_bar_layout.addWidget(title_label)

        # 最小化按钮
        btn_minimize = QPushButton("_", self)
        btn_minimize.setFixedSize(30, 30)
        btn_minimize.clicked.connect(self.showMinimized)
        btn_minimize.setStyleSheet("background: transparent; color: #FFFFFF; border: none; font-size: 18px;")
        title_bar_layout.addWidget(btn_minimize)

        # 关闭按钮
        btn_close = QPushButton("X", self)
        btn_close.setFixedSize(30, 30)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("background: transparent; color: #FFFFFF; border: none; font-size: 18px;")
        title_bar_layout.addWidget(btn_close)

        # 将自定义标题栏添加到主布局
        main_layout.addLayout(title_bar_layout)

        # 创建终端窗口
        self.terminal_window = TerminalWindow()
        main_layout.addWidget(self.terminal_window)  # 添加终端窗口到布局

        self.setLayout(main_layout)

        # 事件
        self.startPos = None

    def mousePressEvent(self, event):
        """鼠标按下时记录起始位置"""
        if event.button() == Qt.LeftButton:
            self.startPos = event.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动时更新窗口位置"""
        if event.buttons() & Qt.LeftButton and self.startPos is not None:
            self.move(self.pos() + event.pos() - self.startPos)

    def mouseReleaseEvent(self, event):
        """鼠标释放时清空起始位置"""
        if event.button() == Qt.LeftButton:
            self.startPos = None

# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    
    try:
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(window, "未处理的异常", f"程序发生错误: {str(e)}")
        sys.exit(1)
