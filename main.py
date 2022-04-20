from time import sleep
from bot import CryptoBotClient
import logging

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    crypto_client = CryptoBotClient()
    crypto_client.establish_connection()

    while True:
        ticks = crypto_client.get_ticks('BTCUSDT')
        last_rsi_tick = ticks['RSI'].iloc[-1]
        previous_rsi_tick = ticks['RSI'].iloc[-2]
        if last_rsi_tick <= 40 and previous_rsi_tick > 40:
            crypto_client.market_order('BTCUSDT', 'BUY', '0.05')
        if last_rsi_tick >= 70 and previous_rsi_tick < 70:
            crypto_client.market_order('BTCUSDT', 'SELL', '0.05')

        sleep(60)
