import logging
from binance.error import ClientError
from binance.spot import Spot


class Trade:
    def __init__(self, client: Spot, **kwargs):
        self.client = client
        self.params = dict(kwargs.items())
        self.__logger = logging.getLogger('trade_handler')
        self.execute_order()

    def __del__(self):
        self.cancel_order(self.symbol, self.stop_loss_id)
        self.sell()

    def set_stop_loss(self, stop_price: float, tp_price: float):
        params = {
            'symbol': f"{self.symbol}",
            'side': 'SELL',
            'type': 'STOP_LOSS_LIMIT',
            'quantity': self.quantity,
            'stopPrice': stop_price,
            'price': tp_price,
            'timeInForce': 'GTC'
        }
        try:
            self.stop_loss = self.client.new_order(**params)
            self.__logger.info(f'STOP LOSS USTAWIONY - {self.quantity} {self.symbol} @ {stop_price}')
        except ClientError as e:
            self.__logger.error(f'Nie udalo sie wykonac zlecenia: {e}')

    def execute_order(self):
        try:
            self.info = self.client.new_order(**self.params)
            if self.params['side'] == 'BUY':
                self.set_stop_loss(stop_price=self.price * 0.975, tp_price=self.price * 1.025)
            self.__logger.info(f"Wykonano zlecenie {self.side} - {self.quantity} {self.symbol} @ {self.price}")
        except ClientError as e:
            self.__logger.error(f'Nie udalo sie wykonac zlecenia: {e}')

    def cancel_order(self, symbol: str, order_id: int):
        self.client.cancel_order(symbol, orderId=order_id)
        self.__logger.info(f"Anulowano zlecenie {order_id}")

    def update_stop_loss(self):
        self.cancel_order(self.symbol, self.stop_loss_id)
        curr_price = self.client.avg_price(self.symbol)
        stop_price = curr_price * 0.975
        tp_price = curr_price * 1.025
        self.set_stop_loss(stop_price=stop_price, tp_price=tp_price)
        self.__logger.info(f'Zaktualizowano Stop Lossa: nowy SL @ {stop_price}')

    def sell(self):
        params = {
            'symbol': self.symbol,
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': self.quantity,
        }
        self.info = self.client.new_order(**params)
        self.__logger.info(f'Zamknieto pozycje {self.symbol} @ {self.price}')

    @property
    def side(self):
        return self.params['side']

    @property
    def quantity(self):
        return self.params['quantity']

    @property
    def symbol(self):
        return self.params['symbol']

    @property
    def price(self):
        return self.info['fills']['price']

    @property
    def trade_id(self):
        return self.info['orderId']

    @property
    def stop_loss_id(self):
        return self.stop_loss['orderId']
