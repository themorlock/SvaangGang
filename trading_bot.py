
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
		data = self._client.fetch_ohlcv("BTC/USD", timeframe=t, since=last)

		if self._timeframe == "3m":
			return data[::3]

		return data 


	async def start(self):

		sell_hits = 0
		buy_hits = 0

		sell_size = 0
		buy_size = 0

		size = 0.1

		while True:

			current_price = self._curr_price() 

			bal = self._client.fetch_balance()["BTC"]

			free = bal["free"]

			data = self._get_history(count=self._orders)
			rsi = processor.calc_rsi(data)

			self._logger.info("RSI: {}".format(rsi))

			if rsi >= self._sell:
				amt = processor.buy_func(free * size, sell_hits)

				if amt <= free:
					amt = int(amt * current_price)
					self._client.create_market_sell_order(symbol=self._symbol, amount=amt)

					self._logger.info("Selling {0: < 4} at {1}".format(
						amt + buy_size, current_price))

					sell_size += amt
					sell_hits += 1
					buy_hits = 0
					buy_size = 0


			elif rsi <= self._buy:
				amt = processor.buy_func(free * size, buy_hits)

				if amt <= free:
					amt = int(amt * current_price)
					self._client.create_market_buy_order(symbol=self._symbol, amount=amt)

					self._logger.info("Buying {0: < 4} at {1}".format(
						amt + sell_size, current_price))

					sell_size = 0
					sell_hits = 0
					buy_size += amt
					buy_hits += 1


			tot = bal["total"]
			self._logger.info("Current Balance: {0} BTC {1} USd".format(
				round(tot, 6), round(tot * current_price, 4)))

			await asyncio.sleep(int(self._interval * 60))

