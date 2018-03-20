
from indicator import Indicator


class RSI(Indicator):
	def __init__(self, utils, config, logger):
		Indicator.__init__(self, utils, config, logger)

		self.timeframe = self.conf["timeframe"]
		self.distance = self.conf["distance"]
		self.period = self.conf["period"]
		self.sell = self.conf["sell"]
		self.buy = self.conf["buy"]


	def calc_rsi(self, prices: list) -> float:
		period = self.period
		max_len = period if period < len(prices) else len(prices)

		losses = []
		gains = []

		for i in range(1, max_len):
			try:
				change = prices[i] - prices[i-1]
				if change < 0:
					losses.append(abs(change))
				elif change > 0:
					gains.append(change)

			except TypeError as e:
				print(e, prices)

		avg_loss = sum(losses) / period
		avg_gain = sum(gains) / period

		for i in range(period, len(prices)):
			change = prices[i] - prices[i - 1]
			loss = abs(change) if change < 0 else 0
			gain = change if change > 0 else 0

			avg_gain = (avg_gain * (period - 1) + gain) / period
			avg_loss = (avg_loss * (period - 1) + gain) / period

		if avg_loss == 0:
			return 100

		elif avg_gain == 0:
			return 0

		rs = avg_gain / avg_loss
		rsi = round(100 - (100 / (1 + rs)), 2)

		return rsi


	async def acalc_rsi(self, symbol: str):
		data = await self.utils.get_historical_data(symbol, 
			length=self.distance * self.timeframe)

		rsi = self.calc_rsi(data)
		self.logger.debug(rsi)

		return rsi


	async def analyze(self, symbol: str) -> str:
		rsi = await self.acalc_rsi(symbol)

		if rsi >= self.sell:
			return symbol, rsi, "SELL"
		elif rsi <= self.buy:
			return symbol, rsi, "BUY"

		return symbol, rsi, "HOLD"


	def __str__(self):
		return "RSI"

	__repr__ = __str__
