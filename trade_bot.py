
import asyncio

from bitmex import bitmex

class Bot:
	def __init__(self, config: dict, logger=None, client=None):
		self._config = config
		self._logger = logger # todo add logger

		self._api_secret = config["API_SECRET"]
		self._api_key = config["API_KEY"]
		self._symbol = config["SYMBOL"]

		self._rsi_interval = config["RSI_INTERVAL"]
		self._rsi_period = config["RSI_PERIOD"]
		self._orders = config["ORDERS_PER_RSI"]
		self._test = config["TEST"]

		self._client = client if client else bitmex(test=self._test, 
			api_key=self._api_key, api_secret=self._api_secret) 


	def _get_prices(self, count=1) -> float:
		return self._client.Quote.Quote_get(symbol=self._symbol, 
			reverse=True, count=count).result()[0]

	
	def _calc_rsi(self):

		interval = self._rsi_interval
		quotes = self._get_prices(count=self._orders)[::-1]

		for i in quotes:
			logger.debug((i["timestamp"], i["bidPrice"]))

		prices = [float(i["bidPrice"]) for i in quotes]
		
		max_len = interval if interval < len(prices) else len(prices)

		losses = []
		gains = []

		for i in range(1, max_len):
			change = prices[i] - prices[i-1]
			if change < 0:
				losses.append(abs(change))
			elif change > 0:
				gains.append(change)

		avg_loss = sum(losses) / interval
		avg_gain = sum(gains) / interval

		# only iterates through if len(prices) > interval
		for i in range(interval, len(prices)):
			change = prices[i] - prices[i-1]

			loss = abs(change) if change < 0 else 0
			gain = change if change > 0 else 0

			avg_gain = (avg_gain * (interval - 1) + gain) / interval
			avg_loss = (avg_loss * (interval - 1) + gain) / interval

		if avg_loss == 0:
			return 100
		elif avg_gain == 0:
			return 0

		RS = avg_gain / avg_loss
		RSI = round(100 - (100 / (1 + RS)), 2)

		return RSI


	async def start(self):

		sells = 1
		buys = 2
		contracts_to_buy = 60

		while True:
			rsi = self._calc_rsi()
			self._logger.info("RSI: {}".format(rsi))

			curr_price = self._get_prices(count=1)[0]["bidPrice"]
			if rsi >= 75:
				self._logger.info("Selling...")
				self._client.Order.Order_new(symbol=self._symbol, orderQty=(buys * 2),
					price=curr_price).result()

				sells = sells + contracts_to_buy
				buys = 0

			elif rsi <= 30:
				self._logger.info("Buying...")
				self._client.Order.Order_new(symbol=self._symbol, orderQty=-(sells * 2), 
					price=curr_price).result()

				buys = buys + contracts_to_buy
				sells = 0

			else:
				self._logger.info("Holding")

			await asyncio.sleep(int(self._rsi_period * 10))
