import sys
import logging
import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']    # 设置字体，防止中文显示为方块  
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox,
                            QSizePolicy, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from strategy import TradingStrategy
from exchange_interface import ExchangeInterface
import mplfinance as mpf
import pandas as pd

class TradingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.strategy = TradingStrategy()
        self.initUI()
        
        # 数据更新线程
        self.data_thread = DataThread(self.strategy)
        self.data_thread.update_signal.connect(self.update_gui)
        self.data_thread.error_occurred.connect(self.show_error)
        
        # 设置窗口标题和大小
        self.setWindowTitle('欧易量化交易系统 - 实时行情')
        self.resize(1200, 800)
        
        # 初始化交易所设置
        self.on_exchange_changed(self.exchange_combo.currentText())
        self.on_proxy_state_changed()

    def toggle_trading(self):
        if self.start_btn.text() == '开始交易':
            # 更新交易所设置
            self.on_exchange_changed(self.exchange_combo.currentText())
            self.on_proxy_state_changed()
            
            # 更新资金管理器的余额
            try:
                new_balance = float(self.balance_input.text())
                self.strategy.fund_manager.balance = new_balance
            except ValueError:
                QMessageBox.warning(self, '输入错误', '请输入有效的余额数值')
                return
            
            # 获取当前选择的K线周期
            timeframe_map = {
                '1分钟': '1m',
                '3分钟': '3m',
                '5分钟': '5m',
                '15分钟': '15m'
            }
            selected_timeframe = self.timeframe_combo.currentText()
            timeframe = timeframe_map.get(selected_timeframe, '1m')
            
            # 如果线程已经在运行，先停止它
            if hasattr(self.data_thread, 'running') and self.data_thread.running:
                self.data_thread.stop()
            
            # 重新初始化数据线程
            self.data_thread = DataThread(self.strategy)
            self.data_thread.update_signal.connect(self.update_gui)
            self.data_thread.error_occurred.connect(self.show_error)
            self.data_thread.timeframe = timeframe
            
            # 启动数据线程
            self.data_thread.running = True
            self.data_thread.start()
            self.start_btn.setText('停止交易')
            QMessageBox.information(self, '交易开始', f'实时行情监控已启动，将以{selected_timeframe}K线自动更新')
        else:
            # 停止数据线程
            self.data_thread.stop()
            self.start_btn.setText('开始交易')
            QMessageBox.information(self, '交易停止', '实时行情监控已停止')

    def initUI(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        
        # 左侧控制面板
        control_panel = QWidget()
        control_panel.setFixedWidth(250)  # 设置固定宽度
        control_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # 固定宽度策略
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        # 交易所选择
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(['okx', 'binance'])
        self.exchange_combo.currentTextChanged.connect(self.on_exchange_changed)
        control_layout.addWidget(QLabel('交易所选择:'))
        control_layout.addWidget(self.exchange_combo)

        # 代理设置
        self.use_proxy_checkbox = QCheckBox('使用代理')
        self.use_proxy_checkbox.setChecked(True)
        self.use_proxy_checkbox.stateChanged.connect(self.on_proxy_state_changed)
        self.proxy_input = QLineEdit('http://127.0.0.1:10809')
        control_layout.addWidget(self.use_proxy_checkbox)
        control_layout.addWidget(QLabel('代理设置:'))
        control_layout.addWidget(self.proxy_input)
        
        # 参数设置
        self.balance_input = QLineEdit(str(self.strategy.fund_manager.balance))
        self.risk_input = QLineEdit(str(5))  # 默认5%
        
        # 交易模式选择
        self.mode_switch = QCheckBox('实盘模式')
        self.start_btn = QPushButton('开始交易')
        self.start_btn.clicked.connect(self.toggle_trading)

        control_layout.addWidget(QLabel('初始金额:'))
        control_layout.addWidget(self.balance_input)
        control_layout.addWidget(QLabel('风险比例(%):'))
        control_layout.addWidget(self.risk_input)
        control_layout.addWidget(self.mode_switch)
        control_layout.addWidget(self.start_btn)
        
        # 添加参数管理按钮
        self.save_btn = QPushButton('保存策略参数')
        self.load_btn = QPushButton('加载策略参数')
        self.save_btn.clicked.connect(lambda: self.strategy.fund_manager.save_params())
        self.load_btn.clicked.connect(lambda: self.strategy.fund_manager.load_params())
        control_layout.addWidget(self.save_btn)
        control_layout.addWidget(self.load_btn)
        
        # 添加行情获取按钮
        self.fetch_btn = QPushButton('获取行情')
        self.fetch_btn.clicked.connect(self.fetch_market_data)
        control_layout.addWidget(self.fetch_btn)
        
        # 添加K线周期选择和获取按钮
        kline_frame = QFrame()
        kline_layout = QHBoxLayout()
        kline_layout.setContentsMargins(0, 0, 0, 0)
        kline_frame.setLayout(kline_layout)
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['1分钟', '3分钟', '5分钟', '15分钟'])
        self.fetch_kline_btn = QPushButton('获取K线')
        self.fetch_kline_btn.clicked.connect(self.fetch_kline)
        
        kline_layout.addWidget(self.timeframe_combo)
        kline_layout.addWidget(self.fetch_kline_btn)
        
        control_layout.addWidget(QLabel('K线周期:'))
        control_layout.addWidget(kline_frame)
        
        # 添加弹性空间，使控件靠上对齐
        control_layout.addStretch(1)
        
        # 右侧图表
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        layout.addWidget(control_panel)
        layout.addWidget(self.canvas)
        main_widget.setLayout(layout)

        # 数据更新线程
        self.data_thread = DataThread(self.strategy)
        self.data_thread.update_signal.connect(self.update_gui)
        self.data_thread.error_occurred.connect(self.show_error)

        # 添加日志输出
        logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('K线数据')

        # 初始化交易所设置
        self.on_exchange_changed(self.exchange_combo.currentText())
        self.on_proxy_state_changed()

    def on_exchange_changed(self, exchange_name):
        self.strategy.exchange = ExchangeInterface(
            exchange_name=exchange_name,
            simulated=not self.mode_switch.isChecked(),
            proxy=self.proxy_input.text() if self.use_proxy_checkbox.isChecked() else None,
            use_proxy=self.use_proxy_checkbox.isChecked()
        )

    def on_proxy_state_changed(self):
        proxy = self.proxy_input.text() if self.use_proxy_checkbox.isChecked() else None
        self.strategy.exchange.set_proxy(proxy)
        self.proxy_input.setEnabled(self.use_proxy_checkbox.isChecked())

    def show_error(self, message):
        QMessageBox.critical(self, '错误', message)
    
    def update_gui(self, data):
        self.balance_input.setText(str(round(data['balance'], 2)))
        
        # 转换K线数据格式
        df = pd.DataFrame(data['ohlcv'], 
                         columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        
        # 检查数据是否为空
        if df.empty:
            self.logger.error("获取的K线数据为空")
            return
            
        # 清空图表并绘制K线
        self.ax.clear()
        
        # 获取当前周期和交易对
        timeframe = data.get('timeframe', '1m')
        symbol = data.get('symbol', 'BTC/USDT')
        
        # 转换周期显示格式
        timeframe_display = {
            '1m': '1分钟',
            '3m': '3分钟',
            '5m': '5分钟',
            '15m': '15分钟'
        }.get(timeframe, timeframe)
        
        try:
            # 使用mplfinance绘制K线图
            mpf.plot(df, type='candle', ax=self.ax, style='charles',
                    ylabel='价格',
                    volume=True,  # 显示成交量
                    mav=(5, 10),  # 添加5日和10日移动平均线
                    warn_too_much_data=1000)
            
            # 手动设置标题，包含更新时间和周期
            current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ax.set_title(f'{self.exchange_combo.currentText().upper()} {symbol} {timeframe_display}K线 (更新: {current_time})')
            
            # 优化图表显示
            self.ax.grid(True, alpha=0.3)
            
            # 强制重绘画布，使用更高效的方式
            self.canvas.draw()
            
            # 记录日志
            self.logger.info(f'K线图已更新: {symbol} {timeframe_display} 数据点数: {len(df)}')
            
        except Exception as e:
            self.logger.error(f'绘制K线图失败: {str(e)}')
            return

    def fetch_market_data(self):
        try:
            # 获取市场数据
            market_data = self.strategy.exchange.get_market_data('BTC/USDT')
            ticker = market_data['ticker']
            
            # 显示最新价格信息
            message = f"当前价格: {ticker['last']}\n开盘价: {ticker['open']}\n最高价: {ticker['high']}\n最低价: {ticker['low']}\n24小时成交量: {ticker['volume']}\n"
            
            # 如果数据线程未运行，则手动获取一次K线数据并更新图表
            if not hasattr(self.data_thread, 'running') or not self.data_thread.running:
                # 获取K线数据
                timeframe_map = {
                    '1分钟': '1m',
                    '3分钟': '3m',
                    '5分钟': '5m',
                    '15分钟': '15m'
                }
                selected_timeframe = self.timeframe_combo.currentText()
                timeframe = timeframe_map.get(selected_timeframe, '1m')
                
                ohlcv = self.strategy.exchange.get_ohlcv('BTC/USDT', timeframe)
                
                # 更新图表
                data = {
                    'balance': self.strategy.fund_manager.balance,
                    'ohlcv': ohlcv,
                    'timeframe': timeframe,
                    'symbol': 'BTC/USDT'
                }
                self.update_gui(data)
            
            QMessageBox.information(self, '市场数据', message)
            
        except Exception as e:
            QMessageBox.critical(self, '获取失败', f'获取市场数据失败: {str(e)}')
    
    def fetch_kline(self):
        try:
            # 获取选择的时间周期
            timeframe_map = {
                '1分钟': '1m',
                '3分钟': '3m',
                '5分钟': '5m',
                '15分钟': '15m'
            }
            selected_timeframe = self.timeframe_combo.currentText()
            timeframe = timeframe_map.get(selected_timeframe, '1m')
            
            # 更新数据线程的时间周期
            if hasattr(self.data_thread, 'timeframe'):
                self.data_thread.update_timeframe(timeframe)
                self.logger.info(f'已更新K线周期为: {selected_timeframe}')
            
            # 获取K线数据
            ohlcv = self.strategy.exchange.get_ohlcv('BTC/USDT', timeframe)
            
            # 转换数据格式
            df = pd.DataFrame(ohlcv, 
                             columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df.set_index('time', inplace=True)
            
            # 检查数据是否为空
            if df.empty:
                self.logger.error("获取的K线数据为空")
                return
                
            # 清空图表并绘制K线
            self.ax.clear()
            
            # 使用mplfinance绘制K线图
            mpf.plot(df, type='candle', ax=self.ax, style='charles',
                    ylabel='价格',
                    volume=False,
                    warn_too_much_data=1000)
            
            # 手动设置标题，包含更新时间和周期
            current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ax.set_title(f'{self.exchange_combo.currentText().upper()} BTC/USDT {selected_timeframe}K线 (更新: {current_time})')
            
            # 强制重绘画布
            self.canvas.draw_idle()
            self.canvas.flush_events()
            
            # 如果数据线程正在运行，提示用户已更新周期
            if hasattr(self.data_thread, 'running') and self.data_thread.running:
                QMessageBox.information(self, '更新成功', f'已切换到{selected_timeframe}K线，将持续更新')
            else:
                QMessageBox.information(self, '获取成功', f'成功获取{selected_timeframe}K线数据')
            
        except Exception as e:
            QMessageBox.critical(self, '获取失败', f'获取K线数据失败: {str(e)}')

class DataThread(QThread):
    update_signal = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, strategy, parent=None):
        super().__init__(parent)
        self.strategy = strategy
        self.running = True
        self.logger = logging.getLogger('K线数据')
        self.retry_count = 0
        self.timeframe = '1m'  # 默认1分钟K线
        self.symbol = 'BTC/USDT'  # 默认交易对

    def run(self):
        last_timestamp = None
        last_timeframe = None
        while self.running:
            try:
                # 应用最新代理设置
                self.strategy.exchange.set_proxy(self.strategy.exchange.proxy)
                ohlcv = self.strategy.exchange.get_ohlcv(self.symbol, self.timeframe)
                
                # 检查是否有新数据或者周期已更改
                current_timestamp = ohlcv[-1][0] if ohlcv and len(ohlcv) > 0 else None
                timeframe_changed = last_timeframe != self.timeframe
                
                # 如果时间戳不同或周期已更改，则更新图表
                if current_timestamp != last_timestamp or timeframe_changed:
                    last_timestamp = current_timestamp
                    last_timeframe = self.timeframe
                    self.retry_count = 0
                    self.logger.info(f'获取K线数据成功 时间戳: {current_timestamp} 周期: {self.timeframe}')
                    
                    data = {
                        'balance': self.strategy.fund_manager.balance,
                        'ohlcv': ohlcv,
                        'timeframe': self.timeframe,
                        'symbol': self.symbol
                    }
                    self.update_signal.emit(data)
                
                # 根据K线周期动态调整更新间隔
                # 统一设置为3秒更新一次，提高更新频率
                self.msleep(3000)  # 固定3秒更新一次
                
            except Exception as e:
                self.retry_count += 1
                error_msg = f'网络错误: {str(e)}\n已重试 {self.retry_count}/3 次'
                self.error_occurred.emit(error_msg)
                if self.retry_count >= 3:
                    self.stop()
                self.msleep(3000)

    def stop(self):
        self.running = False
        self.wait()
        
    def update_timeframe(self, timeframe):
        """更新K线周期"""
        self.timeframe = timeframe
        self.logger.info(f'K线周期已更新为: {timeframe}')
        # 重置时间戳检查，确保下次循环立即更新图表
        return timeframe



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TradingGUI()
    ex.show()
    sys.exit(app.exec_())