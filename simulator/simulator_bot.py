
import math
import json
import sys

sys.path.append("../helpers")

import processor


DATA_FILE = "data.json"
RSI_PERIOD = 7


def load_data(file):
	with open(file, "r") as f:
		return json.load(f)


def buy_func(base_size: int, hits: int):
	return base_size * (hits + 1)


def main():
	btc_bal = 0.1
	usd_bal = 100

	size = 0.1 # percent

	sell = 70
	buy = 30

	data = load_data(DATA_FILE)

	sell_hits = 0
	buy_hits = 0

	price = data[0][4]
	print("Start!\nBtc Bal: {0: < 10} | Usd Bal: {1: < 10} \
		| Total Btc: {2: < 10} | Total Usd: {3: < 10}".format(
		round(btc_bal, 4), round(usd_bal, 4), 
		round(btc_bal + usd_bal / price, 4),
		round(btc_bal * price + usd_bal, 4)))

	p = RSI_PERIOD
	for i in range(p, len(data), 1):
		rsi = processor.calc_rsi(data[i-p:i], period=p)

		price = data[i][4]

		did_something = False
		if rsi <= buy:
			amt = buy_func(size * usd_bal, buy_hits)

			btc_bal += amt / price
			usd_bal -= amt

			sell_hits = 0
			buy_hits += 1

			did_something = True

		elif rsi >= sell:
			amt = buy_func(size * btc_bal, sell_hits)

			btc_bal -= amt
			usd_bal += amt * price

			sell_hits += 1
			buy_hits = 0

			did_something = True


		# if did_something:

	print("End!\nBtc Bal: {0: < 10} | Usd Bal: {1: < 10} \
		| Total Btc: {2: < 10} | Total Usd: {3: < 10}".format(
		round(btc_bal, 4), round(usd_bal, 4), 
		round(btc_bal + usd_bal / price, 4),
		round(btc_bal * price + usd_bal, 4)))


if __name__ == '__main__':
	main()