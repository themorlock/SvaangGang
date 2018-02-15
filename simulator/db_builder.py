
from datetime import datetime, timedelta
import json
import time
import os

import ccxt


def main():

	bitmex = ccxt.bitmex()

	file = "test.json"

	data = []

	t = "1m"
	time_period = 1 # using minutes
	amt = 500

	target = datetime(2018, 1, 16, 1, 14) - timedelta(days=330)

	last = datetime(2018, 1, 16, 1, 14) - timedelta(minutes=time_period*amt-1)
	while(target < last):
		try:
			d = bitmex.fetch_ohlcv("BTC/USD", "1m", since=last.timestamp()*1000, limit=amt)[::-1]

			data.extend(d)

			last -= timedelta(minutes=time_period*amt-1)
		
		except ccxt.DDoSProtection as e:
			print(e)


		time.sleep(2) # bitmex timer, you can soemtimes get around not using it


	with open("data.json", "r") as f:
		json.dump(data, f)

	print(target, last)

if __name__ == '__main__':
	main()
