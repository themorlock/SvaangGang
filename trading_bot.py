
from datetime import datetime, timedelta
import tenacity
import logging
import asyncio
import sys

import ccxt.async as ccxt

sys.path.append("helpers")
from exchange_processor import ExchangeProcessor


class Bot:
	def __init__(self, config: dict, logger, exchange=None):
		self._config = config
		self._logger = logger

		self._symbol = config["symbol"]

		self._rsi_timeframe = config["rsi_timeframe"]
		self._rsi_period = config["rsi_period"]
		self._rsi_sell = config["rsi_sell"]
		self._rsi_buy = config["rsi_buy"]

		self._purchase_size_percentage = config["purchase_size_percentage"]
		self._update_interval = config["update_interval"]

		if exchange:
			self._exchange = exchange
		else:
			self._exchange = ccxt.bitmex({
				"test": config["test"],
				"apiKey": config["apiKey"],
				"secret": config["secret"]
			})

		self._ep = ExchangeProcessor(self._exchange, self._logger)

		self._aretry = tenacity.AsyncRetrying(
			wait=tenacity.wait_random(0, 2),
			retry=(
				tenacity.retry_if_exception(ccxt.DDoSProtection) | 
				tenacity.retry_if_exception(ccxt.RequestTimeout)
				)
			)

		self._active_markets = {}
		if self._symbol:
			self._active_markets[self._symbol] = {"buys": 0, "sells": 0}


	def _calculate_purchase_size(self, base_purchase_size: int, hits: int):
		return base_purchase_size * (1.61*hits + 1)


	async def start(self):
		await self._aretry.call(exchange.load_markets)

		while True:

			if not self._symbol:
				symbols = [
					symbol for symbol in self._exchange.symbol
					if not symbol.startswith(".")
					]

				tasks = [
					self._acalc_rsi(symbol) 
					for symbol in symbols
					]

				rsi_vals = sorted(
					await asyncio.gather(*tasks, return_exceptions=True).items(),
					lambda x: x[1]
					)

			else:
				rsi_vals = [self._ep.acalc_rsi(self._symbol)]


			for symbol, rsi in rsi_vals:

				available_balance = await self._ep._get_available_balance()
				current_price = await self._ep.get_current_price()
				curr_rsi = await self._ep.acalc_rsi(symbol, self._rsi_period)

				self._logger.info("RSI: is {}".format(current_rsi))

				if curr_rsi >= self._rsi_sell:
					current_order_size = self._calculate_purchase_size(
						available_balance * self._purchase_size_percentage, sell_hits)

					if current_order_size > available_balance:
						current_order_size = available_balance

					current_order_size = int(current_price * current_order_size)

					if curr_bought > 0:
						self._logger.info("Closing previous position by selling {0: < 4} at {1}"\
							.format(curr_bought, current_price))

					self._logger.info("Selling {0: < 4} at {1}".format(
						current_order_size, self._get_current_price()))

					try:
						self._exchange.create_market_sell_order(
							symbol=self._symbol, amount=current_order_size + curr_bought)
					except ccxt.ExchangeEror as e:
						print("Failed order:", e)


					curr_sold += current_order_size
					curr_bought = 0

					sell_hits += 1
					buy_hits = 0 


				elif curr_rsi <= self._rsi_buy:
					current_order_size = self._calculate_purchase_size(
						available_balance * self._purchase_size_percentage, buy_hits)

					if current_order_size > available_balance:
						current_order_size = available_balance

					current_order_size = int(current_price * current_order_size)

					if curr_sold > 0:
						self._logger.info("Closing previous position by buying {0: < 4} at {1}"\
							.format(curr_sold, current_price))

					self._logger.info("Buying {0: < 4} at {1}".format(
						current_order_size, self._get_current_price()))
					
					try:
						self._exchange.create_market_buy_order(
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