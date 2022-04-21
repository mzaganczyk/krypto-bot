import json
import pandas as pd
import logging
from binance.spot import Spot as Client
from trade import Trade
from binance.error import ClientError
from operator import itemgetter


class CryptoBotClient:
    def __init__(self):
        self.__get_credentials()
        self.__connection = False  # okreslanie czy jest uzyskane polaczenie z binance
        self.__logger = logging.getLogger('crypto_bot')
        self.trades = []

    def __get_credentials(self):
        with open('config.json', 'r') as f:
            tmp = json.load(f)
            self.__api_key = tmp['API_KEY']
            self.__secret_key = tmp['SECRET_KEY']

    def establish_connection(self):
        url = 'https://testnet.binance.vision'
        self.client = Client(
            base_url=url, key=self.__api_key, secret=self.__secret_key)
        self.__connection = True
        self.__initial_balance = self.balance
        self.__trade_id = 0
        self.__logger.info('Nawiazano polaczenie.')

    @property
    def stats(self):
        return self.client.account()

    @property
    def balance(self):
        balance_raw = pd.DataFrame(self.stats['balances']).set_index('asset')
        tmp = list(balance_raw.index)
        tmp.remove('USDT')
        tmp.remove('BUSD')
        tmp = {x: self.client.avg_price(f'{x}USDT')['price'] for x in tmp}
        tmp = pd.DataFrame(tmp, index=['price']).T
        tmp = pd.concat([balance_raw, tmp], axis=1).fillna(1).astype(float)
        tmp['usd_balance'] = tmp['price'] * tmp['free'] + tmp['price'] * tmp['locked']
        return tmp

    def market_order(self, symbol: str, side: str, quantity: float):
        if side == 'BUY':
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity,
            }
            self.trades.append(Trade(**params))

    @staticmethod
    def get_rsi(price: pd.Series, periods: int = 14, ema: bool = True):
        """
        Sposob obliczania wziety z: https://www.investopedia.com/terms/r/rsi.asp
        """
        close_delta = price.diff()

        up = close_delta.clip(lower=0)
        down = -1 * close_delta.clip(upper=0)

        if ema:
            ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
            ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
        else:
            ma_up = up.rolling(window=periods, adjust=False).mean()
            ma_down = down.rolling(window=periods, adjust=False).mean()

        rsi = ma_up / ma_down
        rsi = 100 - (100 / (1 + rsi))
        return rsi

    def get_ticks(self, symbol: str, interval: str = '1m', limit: int = 60):
        columns = [
            'Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time',
            'Quote asset volume', 'Number of trades', 'Taker buy base asset volume',
            'Taker buy quote asset volume', 'Ignore'
        ]
        klines = self.client.klines(symbol, interval=interval, limit=limit)
        ticks = pd.DataFrame(klines, columns=columns).astype(float)
        ticks['RSI'] = self.get_rsi(ticks['Close'])
        return ticks
