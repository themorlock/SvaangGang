
from datetime import datetime

import ccxt.async as ccxt
import tenacity

import rsi


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


	async def get_available_balance(self):
		bal = await self._exchange.fetch_balance()
		self._logger.debug(bal)

		print(bal)
		return bal[self._symbol[:self._symbol.index("/")]]["free"]
		

	async def get_current_price(self, symbol: str) -> float:
		ticker = await self._aretry.call(self._exchange.fetch_ticker, symbol)
		self._logger.debug(ticker)

		return ticker["last"]


	async def _curr_timestamp(self, symbol: str):
		ticker = await self._aretry.call(self._exchange.fetch_ticker, symbol)

		return ticker["timestamp"]


	async def _get_historical_data(self, symbol: str, length: int):
		base = await self._curr_timestamp(symbol)
		base /= 1000
		
		since = datetime.fromtimestamp(base) - timedelta(minutes=length)
		since = since.timestamp() * 1000

		prices = await self._aretry.call(self._exchange.fetch_ohlcv, 
			self._symbol, "1m", since=since)

		close_prices = [p[4] for p in prices]

		self._logger.debug(close_prices)

		return close_prices