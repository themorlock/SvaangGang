
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

				if amt > 0:
					self._client.create_market_sell_order(symbol=self._symbol, amount=amt)


				self._logger.info("Selling {0: < 4} at {1}".format(amt, current_price))

				sell_hits += 1
				buy_hits = 0


			elif rsi <= self._buy:
				amt = processor.buy_func(free * size, sell_hits)

				if amt > 0:
					self._client.create_market_sell_order(symbol=self._symbol, amount=amt)

<<<<<<< HEAD
=======
    async def start(self):
        previous_rsis = [-1]
        midway_traded = False
        order_book = []
        
        while True:
>>>>>>> a064b837fc707bd79cd688b4194ef783253d09e1

				sell_hits = 0
				buy_hits += 1

				self._logger.info("Buying {0: < 4} at {1}".format(amt, current_price))


			current_price = self._curr_price()

			btc = float(bal["total"])
			self._logger.info("Curr BTC Bal: {0: <8} | Curr USD Bal: {1: <8}".format(
				round(btc, 4), round(btc * current_price, 4)))

			await asyncio.sleep(int(self._interval * 60))

<<<<<<< HEAD
=======
                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Bought Midway!")
                    midway_traded = True

                elif all(0 <= previous_rsi <= self._buy_threshold for previous_rsi in previous_rsis):
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_midpoint_order_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Selling Midway...")

                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold Midway!")
                    midway_traded = True

            elif rsi >= self._sell_threshold:
                try:
                    current_order_qty = self._contract_purchase_size
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_buy_turnover_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Selling...")
                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_sell_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold!")
                    midway_traded = False

                except:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"])
                            order_book.pop(i)
                            break
                    self._logger.info("Selling...")
                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_sell_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold!")
                    midway_traded = False

            elif rsi <= self._buy_threshold:
                try:
                    current_order_qty = self._contract_purchase_size
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_sell_turnover_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Buying...")

                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Bought!")
                    midway_traded = False

                except:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = int(order_book[i]["orderQty"])
                            order_book.pop(i)
                            break
                    self._logger.info("Buying...")

                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)

                    self._logger.info("Successfully Bought!")

                    midway_traded = False
            else:
                self._logger.info("Holding")

            if len(previous_rsis) == self._rsi_previous_hits:
                previous_rsis.pop(0)

            previous_rsis.append(rsi)

            self._logger.info("Curr Balance {}".format(
                self._client.fetch_balance()["total"]["BTC"]))

            await asyncio.sleep(int(self._update_interval * 60))
>>>>>>> a064b837fc707bd79cd688b4194ef783253d09e1
