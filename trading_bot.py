
from datetime import datetime
import asyncio
import sys

from ccxt import bitmex

sys.path.append("helpers")
import processor


class Bot:
	def __init__(self, config: dict, logger=None, client=None):
		self._config = config
		self._logger = logger

		self._symbol = config["symbol"]

		self._rsi_timeframe = config["rsi_timeframe"]
		self._rsi_period = config["rsi_period"]
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
		return base_purchase_size * (1.61*hits + 1)

	
	def _get_available_balance(self):
		return self._client.fetch_balance()[self._symbol[:self._symbol.index("/")]]["free"]


	def _get_current_price(self) -> float:
		return self._client.fetch_ticker(self._symbol)["close"]


	def _get_historical_data(self):

		dist = self._rsi_period * self._rsi_timeframe
		base = self._client.fetch_ticker("BTC/USD")["timestamp"] / 1000
		since = processor.get_timestamp(dist, base)

		prices = self._client.fetch_ohlcv(self._symbol, "1m", since=since*1000)[:-1]

		close_prices = [p[4] for p in prices]

		self._logger.debug(close_prices)

		return close_prices


	async def start(self):

		sell_hits = 0
		buy_hits = 0

		curr_bought = 0 
		curr_sold = 0

		while True:
			available_balance = self._get_available_balance()
			current_price = self._get_current_price()

			prices = self._get_historical_data()
			current_rsi = processor.calculate_rsi(prices, self._rsi_period)

			self._logger.info("RSI: is {}".format(current_rsi))

			if current_rsi >= self._rsi_sell:
				current_order_size = self._calculate_purchase_size(
					available_balance * self._purchase_size_percentage, sell_hits)

				if current_order_size > available_balance:
					current_order_size = available_balance

				current_order_size = int(current_price * current_order_size)

				if curr_bought > 0:
					self._logger.info("Closing previous position by buying {0: < 4} at {1}"\
						.format(curr_sold, current_price))

				self._logger.info("Selling {0: < 4} at {1}".format(
					current_order_size, self._get_current_price()))

				try:
					self._client.create_market_sell_order(
						symbol=self._symbol, amount=current_order_size + curr_bought)
				except ccxt.ExchangeEror as e:
					print("Failed order:", e)


				curr_sold += current_order_size
				curr_bought = 0

				sell_hits += 1
				buy_hits = 0 


			elif current_rsi <= self._rsi_buy:
				current_order_size = self._calculate_purchase_size(
					available_balance * self._purchase_size_percentage, buy_hits)

				if current_order_size > available_balance:
					current_order_size = available_balance

				current_order_size = int(current_price * current_order_size)

				self._logger.info("Buying {0: < 4} at {1}".format(
					current_order_size, self._get_current_price()))
				
				try:
					self._client.create_market_buy_order(
						symbol=self._symbol, amount=current_order_size + curr_sold)
				except ccxt.ExchangeEror as e:
					print("Failed order:", e)

				curr_bought += current_order_size
				curr_sold = 0

				buy_hits += 1
				sell_hits = 0

			
			else:
				self._logger.info("Holding")

			await asyncio.sleep(self._bot_refresh_speed)