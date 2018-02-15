
from datetime import datetime, timedelta
import asyncio
import sys

from ccxt import bitmex

sys.path.append("helpers/")

import processor

class Bot:
	def __init__(self, config: dict, logger=None, client=None):
		self._config = config
		self._logger = logger

		self._symbol = config["symbol"]

		self._timeframe = config["timeframe"]
		self._rsi_period = config["rsi_period"]
		self._orders = config["orders_per_rsi"]

		self._sell = config["sell"]
		self._buy = config["buy"]

		self._interval = config["interval"]

		if client:
			self._client = client

		else: 
			self._client = bitmex({
				"test": config["test"],
				"apiKey": config["key"],
				"secret": config["secret"]
				})


	def _get_timestamp(self, count) -> int:
		if self._timeframe == "1m":
			t = datetime.now() - timedelta(minutes=count)
			return t.timestamp() * 1000

		elif self._timeframe == "3m":
			t = datetime.now() - timedelta(minutes=3*count)
			return t.timestamp() * 1000

		elif self._timeframe == "5m":
			t = datetime.now() - timedelta(minutes=5*count)
			return t.timestamp() * 1000

		elif self._timeframe == "1h":
			t = datetime.now() - timedelta(hours=count)
			return (datetime.now() - timedelta(hours=count)).timestamp() * 1000

		t = datetime.now() - timedelta(days=count)
		return t.timestamp() * 1000


	def _curr_price(self) -> float:
		return self._client.fetch_ticker("BTC/USD")["close"]


	def _get_history(self, count=1) -> float:
		last = self._get_timestamp(count)

		t = self._timeframe
		t = t if t != "3m" else "1m"
		data = self._client.fetch_ohlcv("BTC/USD", timeframe=t, since=last)[::-1]

		if self._timeframe == "3m":
			return data[::3]

		return data 


	async def start(self):

		sell_hits = 0
		buy_hits = 0
		size = 0.1

		while True:

			bal = self._client.fetch_balance()["BTC"]

			print(bal)

			free = bal["free"]

			data = self._get_history(count=self._orders)
			rsi = processor.calc_rsi(data)

			self._logger.info("RSI: {}".format(rsi))

			if rsi >= self._sell:
				amt = processor.buy_func(free * size, sell_hits)

				if amt <= free:
					amt = int(amt * current_price)
					self._client.create_market_sell_order(symbol=self._symbol, amount=amt)


					self._logger.info("Selling {0: < 4} at {1}".format(amt, current_price))

					sell_hits += 1
					buy_hits = 0


			elif rsi <= self._buy:
				amt = processor.buy_func(free * size, sell_hits)

				if amt <= free:
					amt = int(amt * current_price)
					self._client.create_market_sell_order(symbol=self._symbol, amount=amt)

					self._logger.info("Buying {0: < 4} at {1}".format(amt, current_price))

					sell_hits = 0
					buy_hits += 1


			await asyncio.sleep(int(self._interval * 60))

