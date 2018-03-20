
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


	async def close_positions(self, symbol, price=None):
		sells = self._markets[symbol]["curr_sold"]
		buys = self._markets[symbol]["curr_bought"]

		if sells > 0:
			self.logger.info("Buying {0: < 4} to close shorts".format(sells))
		if buys > 0:
			self.logger.info("Selling {0: < 4} to close longs".format(buys))

		if price:
			# buy longs to close shorts
			if sells > 0:
				await self._exchange.create_limit_buy_order(symbol, sells, price)
			# buy shorts to close longs
			if buys > 0:
				await self._exchange.create_limit_sell_order(symbol, buys, price)

		else:
			# buy longs to close shorts
			if sells > 0:
				await self._exchange.create_market_buy_order(symbol, sells)
			# buy shorts to close longs
			if buys > 0:
				await self._exchange.create_market_sell_order(symbol, buys)

		self._markets[symbol]["curr_sold"] = 0
		self._markets[symbol]["curr_bought"] = 0


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

				if heuristic == SELL:
					order_size = await self.util.purchase_size("linear", bal, 
						sells=self._markets[symbol]["sells"])

					if order_size > bal:
						order_size = bal

					order_size = int(curr_p * order_size)

					await self._exchange.create_market_sell_order(symbol, order_size)
					await self.close_positions(symbol)

					self.logger.info("Selling {0: < 4} at {1}".format(
						order_size, curr_p))

					self._markets[symbol]["curr_sold"] += order_size

					self._markets[symbol]["sells"] += 1
					self._markets[symbol]["buys"] = 0 


				elif heuristic == BUY:
					order_size = await self.util.purchase_size("linear", bal, 
						buys=self._markets[symbol]["buys"])

					if order_size > bal:
						order_size = bal

					order_size = int(curr_p * order_size)

					await self._exchange.create_market_buy_order(symbol, order_size)
					await self.close_positions(symbol)

					self.logger.info("Buying {0: < 4} at {1}".format(
						order_size, curr_p))

					self._markets[symbol]["curr_bought"] += order_size

					self._markets[symbol]["sells"] = 0
					self._markets[symbol]["buys"] += 1
			
			await asyncio.sleep(self._update_interval)