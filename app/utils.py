
from datetime import datetime, timedelta

import ccxt.async as ccxt
import tenacity


class Utils:
	def __init__(self, exchange: ccxt.Exchange, logger): 
		self._exchange = exchange
		self._logger = logger

		self._aretry = tenacity.AsyncRetrying(
			wait=tenacity.wait_random(0, 2),
			retry=(
				tenacity.retry_if_exception(ccxt.DDoSProtection) | 
				tenacity.retry_if_exception(ccxt.RequestTimeout)
				)
			)	

		self.purchase_strategies = {

		}

	async def get_available_balance(self):
		bal = await self._exchange.fetch_balance()
		bal = bal["BTC"]["free"]

		self._logger.debug("Balance {0}".format(bal))

		return bal
		

	async def get_current_price(self, symbol: str) -> float:
		ticker = await self._aretry.call(self._exchange.fetch_ticker, symbol)
		self._logger.debug(ticker)

		return ticker["close"]


	async def _curr_timestamp(self, symbol: str):
		ticker = await self._aretry.call(self._exchange.fetch_ticker, symbol)

		return ticker["timestamp"]


	async def get_historical_data(self, symbol: str, length: int):
		base = await self._curr_timestamp(symbol)
		base /= 1000
		
		since = datetime.fromtimestamp(base) - timedelta(minutes=length)
		since = since.timestamp() * 1000

		prices = await self._aretry.call(self._exchange.fetch_ohlcv, 
			symbol, "1m", since=since, limit=length)

		close_prices = [p[4] for p in prices]

		self._logger.debug(close_prices)

		return close_prices


	async def purchase_size(self, strat: str, base: float=0.1, sells=0,
		buys=0, bal=None) -> float:

		if not bal:
			bal = await self.get_available_balance()

		base *= bal

		k = abs(sells-buys)
		if strat == "linear":
			size = (1.61 * k + 1) * base
			if size > bal:
				size = bal

			return size
