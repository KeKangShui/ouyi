import time
from fund_manager import FundManager
from exchange_interface import ExchangeInterface
from config import TRADE_PARAMS

class TradingStrategy:
    def __init__(self):
        self.fund_manager = FundManager(TRADE_PARAMS['initial_balance'])
        self.exchange = ExchangeInterface(simulated=True)
        self.trade_history = []

    def determine_trend(self, symbol):
        """判断市场趋势方向"""
        market_data = self.exchange.get_market_data(symbol)
        current_price = market_data['ticker']['last']
        # 简单趋势判断逻辑：最近价格变化方向
        return 'long' if current_price > market_data['ticker']['open'] else 'short'

    def execute_strategy(self, symbol):
        trend = self.determine_trend(symbol)
        risk = TRADE_PARAMS['risk_percent']
        
        position_params = self.fund_manager.get_trade_params(risk)
        entry_price = self.exchange.get_market_data(symbol)['ticker']['last']
        
        order = self.exchange.create_order(
            symbol=symbol,
            side=trend,
            amount=position_params['position_size'],
            price=entry_price
        )
        
        # 记录交易信息
        self.trade_history.append({
            'timestamp': time.time(),
            'symbol': symbol,
            'direction': trend,
            'size': position_params['position_size'],
            'entry_price': entry_price,
            'liquidation_price': self.fund_manager.get_liquidation_price(entry_price, trend)
        })
        
        return order

    def run_backtest(self, symbol, days):
        results = []
        for _ in range(days * 24):
            order = self.execute_strategy(symbol)
            results.append({
                'timestamp': time.time(),
                'direction': order['side'],
                'size': order['amount'],
                'entry_price': order['price'],
                'pnl': order['filled'] * (order['price'] - self.exchange.get_market_data(symbol)['ticker']['last'])
            })
            time.sleep(3600)
        
        # 导出回测结果
        self.export_backtest_results(results)

    def export_backtest_results(self, results):
        import csv
        from datetime import datetime
        filename = f'backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp','direction','size','entry_price','pnl'])
            writer.writeheader()
            writer.writerows(results)

    def get_performance_report(self):
        """生成绩效报告"""
        return {
            'current_balance': self.fund_manager.balance,
            'total_trades': len(self.trade_history),
            'leverage': self.fund_manager.leverage
        }