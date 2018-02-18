from datetime import datetime, timedelta
import asyncio
import sys

from ccxt import bitmex

class Bot:
    def __init__(self, config: dict, logger=None, client=None):
        self._config = config
        self._logger = logger

        self._symbol = config["symbol"]
        self._time_delay = config["time_delay"]

        self._rsi_period_time = config["rsi_period_time"]
        self._rsi_calculation_period = config["rsi_calculation_period"]
        self._rsi_sell = config["rsi_sell"]
        self._rsi_buy = config["rsi_buy"]

        self._purchase_size_percentage = config["purchase_size_percentage"]

        self._bot_refresh_speed = config["bot_refresh_speed"]

        if client:
            self._client = client
        else:
            self._client = bitmex({
                "test": config["test"],
                "apiKey": config["apiKey"],
                "secret": config["secret"]
            })


    def _calculate_purchase_size(self, base_purchase_size: int, hits: int):
        return base_purchase_size * (hits + 1)

    
    def _get_available_balance(self):
        return self._client.fetch_balance()[self._symbol[:self._symbol.index("/")]]["free"]


    def _get_current_price(self) -> float:
        return self._client.fetch_ticker(self._symbol)["close"]


    def _get_historic_timestamp(self) -> int:
        return (datetime.now() - timedelta(minutes=(self._rsi_period_time * (self._rsi_calculation_period + 1) + self._time_delay))).timestamp() * 1000


    def _get_historical_data(self):
        prices = self._client.fetch_ohlcv(self._symbol, timeframe="1m", since=self._get_historic_timestamp())
        close_prices = []
        for price in prices:
            close_prices.append(price[4])
        return close_prices[::self._rsi_period_time]


    def _calculate_rsi(self):
        prices = self._get_historical_data()

        gains = []
        losses = []
        for i in range(1, len(prices)):
            difference = prices[i] - prices[i - 1]
            if difference < 0:
                losses.append(abs(difference))
            elif difference > 0:
                gains.append(difference)
        
        avg_gain = sum(gains) / self._rsi_calculation_period
        avg_loss = sum(losses) / self._rsi_calculation_period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = (100 - (100 / (1 + rs)))
        return rsi


    async def start(self):

        sell_hits = 0
        buy_hits = 0

        while True:
            current_price = self._get_current_price()
            available_balance = self._get_available_balance()
            current_rsi = self._calculate_rsi()

            self._logger.info("RSI: is {}".format(current_rsi))

            if current_rsi >= self._rsi_sell:
                current_order_size = self._calculate_purchase_size(available_balance * self._purchase_size_percentage, sell_hits)

                if current_order_size < available_balance:
                    current_order_size = int(current_order_size * current_price)
                    self._logger.info("Selling {0: < 4} at {1}".format(current_order_size, self._get_current_price()))
                    self._client.create_market_sell_order(symbol=self._symbol, amount=current_order_size)
                else:
                    self._logger.info("Holding because current balance has insufficient funds")
                sell_hits += 1
                buy_hits = 0

            elif current_rsi <= self._rsi_buy:
                current_order_size = self._calculate_purchase_size(available_balance * self._purchase_size_percentage, buy_hits)

                if current_order_size < available_balance:
                    current_order_size = int(current_order_size * current_price)
                    self._logger.info("Buying {0: < 4} at {1}".format(current_order_size, self._get_current_price()))
                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_size)
                else:
                    self._logger.info("Holding because current balance has insufficient funds")
                buy_hits += 1
                sell_hits = 0
            
            else:
                self._logger.info("Holding")

            await asyncio.sleep(self._bot_refresh_speed)