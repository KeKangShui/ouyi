import ccxt
from config import EXCHANGE_CONFIG
import time

class ExchangeInterface:
    def __init__(self, exchange_name='okx', simulated=True, proxy=None, use_proxy=True):
        self.simulated = simulated
        self.proxy = proxy
        self.exchange_name = exchange_name
        self.use_proxy = use_proxy
        
        # 根据交易所名称创建对应的交易所实例
        if exchange_name in EXCHANGE_CONFIG:
            config = EXCHANGE_CONFIG[exchange_name]
            proxy_settings = proxy or config['proxy'] if use_proxy else None
            
            if exchange_name == 'okx':
                self.exchange = ccxt.okx({
                    'apiKey': config['apiKey'],
                    'secret': config['secret'],
                    'proxy': proxy_settings,
                    'options': {
                        'defaultType': 'swap',
                        'adjustForTimeDifference': True
                    }
                })
            elif exchange_name == 'binance':
                self.exchange = ccxt.binance({
                    'apiKey': config['apiKey'],
                    'secret': config['secret'],
                    'proxy': proxy_settings,
                    'options': {
                        'adjustForTimeDifference': True
                    }
                })
            
            self.exchange.set_sandbox_mode(simulated)
            if not simulated and use_proxy and proxy:
                self.configure_proxy(proxy)

    def configure_proxy(self, proxy):
        if proxy.startswith('http'):
            proxy = proxy.split('//')[1]
        self.exchange.proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def create_order(self, symbol, side, amount, price):
        try:
            return self.exchange.create_order(
                symbol,
                'limit',
                side,
                amount,
                price,
                params={'leverage': 1}
            )
        except ccxt.NetworkError as e:
            print(f'网络错误: {e}')
            time.sleep(5)
            return self.create_order(symbol, side, amount, price)
    
    def get_market_data(self, symbol):
        return {
            'ticker': self.exchange.fetch_ticker(symbol),
            'orderbook': self.exchange.fetch_order_book(symbol)
        }
    
    def set_proxy(self, proxy_settings):
        self.exchange.proxy = proxy_settings

    def get_ohlcv(self, symbol, timeframe='1m', limit=100):
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    def get_balance(self):
        return self.exchange.fetch_balance()['USDT']['free']