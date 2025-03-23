import os

# 交易所配置
EXCHANGE_CONFIG = {
    'okx': {
        'apiKey': os.getenv('OKEX_API_KEY', ''),
        'secret': os.getenv('OKEX_SECRET', ''),
        'proxy': {
            'http': os.getenv('PROXY_HTTP', ''),
            'https': os.getenv('PROXY_HTTPS', '')
        }
    },
    'binance': {
        'apiKey': os.getenv('BINANCE_API_KEY', 'Ctvkdj9f05s0GFeRvDUsFqh7cdNriBgLQ4OI5xC5WgDggxaWf85TeahHq4LtDa1l'),
        'secret': os.getenv('BINANCE_SECRET', 'uThRd2nm6rzDI0bFvnVypE7F4Ga1pKa3a1HdsaMm8m8XYQrjMypX1szwmEcHEu0R'),
        'proxy': {
            'http': os.getenv('PROXY_HTTP', ''),
            'https': os.getenv('PROXY_HTTPS', '')
        }
    }
}

# 交易策略参数
TRADE_PARAMS = {
    'risk_percent': 2.0,  # 风险百分比
    'profit_target': 50.0,  # 盈利目标百分比
    'initial_balance': 100.0  # 初始资金
}