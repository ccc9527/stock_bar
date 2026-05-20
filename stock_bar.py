import sys
import requests
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QMenu
from PySide6.QtCore import Qt, QTimer

class StockBar(QWidget):
    def __init__(self):
        super().__init__()

        # 拖动相关
        self.drag_position = None
        self.start_pos = None

        # 1. 混合指数配置,"us.INX", "us.NDX",
        self.stock_codes = ["sh000001", "sz399300","sh513000","us.INX","us.NDX","sh513310"]
        self.current_index = 0
        self.raw_data_lines = []

        # 2. 窗口属性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # 移除透明背景，改为实色底方便点击
        
        # 3. UI 布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 0, 5, 0)
        self.label = QLabel("正在初始化行情...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_style("#FFFFFF") # 初始白色
        self.layout.addWidget(self.label)

        self.update_position()

        # 4. 定时器
        self.data_timer = QTimer(self) 
        self.data_timer.timeout.connect(self.fetch_all_data)
        self.data_timer.start(600000)
        
        self.display_timer = QTimer(self) 
        self.display_timer.timeout.connect(self.rotate_display)
        self.display_timer.start(10000) # 自动轮播改为5秒，手动点击可随时切

        self.fetch_all_data()

    # --- 新增功能：鼠标点击事件 ---
    def mousePressEvent(self, event):
        """处理鼠标点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录拖动起始位置和鼠标全局位置
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.start_pos = event.globalPosition().toPoint()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键点击：弹出菜单
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        """处理鼠标拖动"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放时，判断是拖动还是点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            # 如果鼠标位置变化很小，视为点击而非拖动
            if self.start_pos is not None:
                move_dist = event.globalPosition().toPoint() - self.start_pos
                if move_dist.manhattanLength() < 10:
                    self.rotate_display()
            self.start_pos = None

    def show_context_menu(self, global_pos):
        """右键菜单退出程序"""
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: white; border: 1px solid #555; }")
        quit_action = menu.addAction("退出程序")
        refresh_action = menu.addAction("立即刷新数据")
        
        action = menu.exec(global_pos)
        if action == quit_action:
            QApplication.quit()
        elif action == refresh_action:
            self.fetch_all_data()

    def update_style(self, color):
        """统一管理样式"""
        # EVA紫底色 #6B46C1
        self.setStyleSheet(f"""
            StockBar {{
                background: #6B46C1;
                border-radius: 4px;
            }}
            QLabel {{
                color: {color};
                font-family: 'Microsoft YaHei';
                font-size: 15px;
                font-weight: bold;
                background: transparent;
            }}
        """)

    def update_position(self):
        screen_geo = QApplication.primaryScreen().geometry()
        avail_geo = QApplication.primaryScreen().availableGeometry()
        taskbar_h = screen_geo.height() - avail_geo.height()
        self.setFixedSize(300, 38)
        x = screen_geo.width() - self.width() - 10
        y = screen_geo.height() - taskbar_h - self.height() - 2
        self.move(x, y)

    def fetch_all_data(self):
        url = f"http://qt.gtimg.cn/q={','.join(self.stock_codes)}"
        try:
            resp = requests.get(url, timeout=5)
            resp.encoding = 'gbk'
            lines = [line.strip() for line in resp.text.split(';') if '~' in line]
            if lines:
                self.raw_data_lines = lines
                if "初始化" in self.label.text():
                    self.update_ui()
        except Exception as e:
            print(f"网络异常: {e}")

    def rotate_display(self):
        if self.raw_data_lines:
            self.current_index = (self.current_index + 1) % len(self.raw_data_lines)
            self.update_ui()
            # 每次手动点击或自动轮播后，重置轮播定时器，防止连续跳动
            self.display_timer.start(5000)

    def update_ui(self):
        try:
            line = self.raw_data_lines[self.current_index]
            content = line.split('"')[1]
            parts = content.split('~')
            
            if "s_sh" in line:
                name, price, change_val, change_pct = parts[1], parts[3], float(parts[4]), f"{parts[5]}%"
            else:
                name, price, change_val, change_pct = parts[1], parts[3], float(parts[31]), f"{parts[32]}%"
            
            color = "#FF4500" if change_val >= 0 else "#00FF00"
            symbol = "▲" if change_val > 0 else "▼"
            
            self.label.setText(f"{name} {price} {symbol}{change_pct}")
            self.update_style(color)
        except Exception as e:
            print(f"解析出错: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockBar()
    window.show()
    sys.exit(app.exec())