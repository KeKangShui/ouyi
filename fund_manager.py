class FundManager:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.position_size = 0.0
        self.leverage = 1
        
    def calculate_position(self, risk_percent):
        """根据风险百分比计算仓位大小"""
        return self.balance * risk_percent / 100 * self.leverage
    
    def update_balance(self, profit):
        initial_balance = self.balance
        self.balance += profit
        
        if profit > 0:
            # 盈利达到50%时自动加仓
            if profit / initial_balance >= 0.5:
                self.leverage += 1
                self.position_size = self.calculate_position(5)  # 默认5%风险
        else:
            # 亏损后重置杠杆并全仓
            self.leverage = 1
            if self.balance <= initial_balance * 0.3:  # 爆仓阈值30%
                self.position_size = self.balance
        
        # 强制平仓后恢复初始仓位
        if self.balance <= initial_balance * 0.1:
            self.leverage = 1
            self.position_size = self.calculate_position(2)
        
    def get_liquidation_price(self, entry_price, position_side):
        """计算爆仓价格"""
        # 2% 波动爆仓
        multiplier = 0.02
        if position_side == 'long':
            return entry_price * (1 - multiplier)
        else:
            return entry_price * (1 + multiplier)

    def get_trade_params(self, risk_percent):
        return {
            'position_size': self.calculate_position(risk_percent),
            'current_balance': self.balance,
            'leverage': self.leverage
        }
    
    def save_params(self, filename='strategy_params.json'):
        import json
        params = {
            'initial_balance': self.balance,
            'leverage': self.leverage,
            'risk_percent': 5  # 默认风险百分比
        }
        with open(filename, 'w') as f:
            json.dump(params, f)

    def load_params(self, filename='strategy_params.json'):
        import json
        try:
            with open(filename) as f:
                params = json.load(f)
                self.balance = params['initial_balance']
                self.leverage = params['leverage']
        except FileNotFoundError:
            print("参数文件不存在，使用默认配置")