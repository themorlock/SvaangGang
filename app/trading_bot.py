
from datetime import datetime, timedelta
import tenacity
import logging
import asyncio
import sys

import ccxt.async as ccxt

from utils import Utils 

HOLD = "HOLD"
SELL = "SELL"
BUY = "BUY"

class Bot:
	def __init__(self, config: dict, logger, exchange):
		self.conf = config
		self.logger = logger
		self._exchange = exchange

		cfg = config.bot

		self._purchase_size_percentage = cfg["purchase_size_percentage"]
		self._update_interval = cfg["update_interval"]
		self._symbol = cfg["symbol"]

		self.util = Utils(self._exchange, self.logger)

		self._aretry = tenacity.AsyncRetrying(
			wait=tenacity.wait_random(0, 2),
			retry=(
				tenacity.retry_if_exception(ccxt.DDoSProtection) | 
				tenacity.retry_if_exception(ccxt.RequestTimeout)
				)
			)

		self._markets = {}
		if self._symbol:
			self._markets[self._symbol] = {
				"curr_sold": 0, "curr_bought": 0, "buys": 0, "sells": 0
				}


	async def get_symbols(self):
		if self._symbol:
			return (self._symbol,)

		symbols = [
			symbol for symbol in self._exchange.symbol
			if not symbol.startswith(".")
			]

		return symbols


	async def start(self):
		await self._aretry.call(self._exchange.load_markets)

		indicator = self.conf.bot["indicator"]
		indicator = self.conf.indicators[indicator](
			self.util, self.conf.c_indicators[indicator], self.logger)

		while True:

			symbols = await self.get_symbols()

			tasks = [
				indicator.analyze(symbol) 
				for symbol in symbols
				]

			indications = await asyncio.gather(*tasks)

			for symbol, val, heuristic in indications:

				bal = await self.util.get_available_balance()
				curr_p = await self.util.get_current_price(symbol)

				self.logger.info("{0}'s {1} is {2} and heuristic is {3}".format(
					symbol, indicator, val, heuristic))

				market = self._markets[symbol]
				if heuristic == SELL:
					order_size = await self.util.purchase_size("linear", bal, 
						sells=market["sells"])

					if order_size > bal:
						order_size = bal

					order_size = int(curr_p * order_size)
					market["curr_sold"] += order_size

					self.logger.info("Selling {0: < 4} at {1}".format(
						order_size, curr_p))

					addnl = market["curr_bought"]
					if addnl > 0:
						self.logger.info("Buying {0: < 4} to close open shorts".format(
						addnl))
						order_size += addnl
						market["curr_bought"] = 0

					await self._exchange.create_market_sell_order(symbol, order_size)

					market["sells"] += 1
					market["buys"] = 0

				elif heuristic == BUY:
					order_size = await self.util.purchase_size("linear", bal, 
						buys=market["buys"])

					if order_size > bal:
						order_size = bal

					order_size = int(curr_p * order_size)
					market["curr_bought"] += order_size

					self.logger.info("Buying {0: < 4} at {1}".format(
						order_size, curr_p))

					addnl = market["curr_sold"]
					if addnl > 0:
						self.logger.info("Buying {0: < 4} to close open shorts".format(
						addnl))
						order_size += addnl
						market["curr_sold"] = 0

					await self._exchange.create_market_buy_order(symbol, order_size)

					market["sells"] = 0
					market["buys"] += 1

				self._markets[symbol] = market
			
			await asyncio.sleep(self._update_interval)