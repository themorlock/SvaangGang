
from datetime import datetime
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


def lin_buy_func(base_size: int, hits: int, k: int = 4):
	return base_size * (k*hits + 1)


def sig_buy_func(max_balance: float, hits: int, k: int = 1):
	return max_balance / (1 + math.exp(-(k*hits - 5)))
						  

def run_simul(data: list, buy_func, btc_bal: float = 0.1, usd_bal: float = 100,
		order_size: float = 0.1, rsi_sell: int = 70,
		rsi_buy: int = 30, rsi_period: int = 14,
		orders_per_rsi: int = 14, return_hist: bool = False):

	sell_hits = 0
	buy_hits = 0

	if return_hist:
		hist = {}

	for i in range(orders_per_rsi, len(data)):
		rsi = processor.calc_rsi(data[i - orders_per_rsi:i], rsi_period)

		price = data[i][4]

		# TIME TO BUY
		if rsi <= rsi_buy:
			base = usd_bal * order_size
			amt = buy_func(base, buy_hits)

			if amt <= usd_bal:
				usd_bal -= amt
				btc_bal += amt / price

				sell_hits = 0
				buy_hits += 1

				#  print("buying {0} hits {1}".format(amt, buy_hits-1))

		# TIME TO SELL
		elif rsi >= rsi_sell:
			base = btc_bal * order_size
			amt = buy_func(base, sell_hits)

			if amt <= btc_bal:
				usd_bal += amt * price
				btc_bal -= amt

				sell_hits += 1
				buy_hits = 0

				#  print("selling {0} hits {1}".format(amt*price, sell_hits-1))

		if return_hist:
			hist[data[i][0]] = {"usd_bal": usd_bal, "btc_bal": btc_bal}

	if return_hist:
		return (btc_bal, usd_bal, hist)

	return (btc_bal, usd_bal)
			  

def main():
	btc_bal = 0.1
	usd_bal = 100

	size = 0.1 # percent

	sell = 70
	buy = 30

	order_size = [0.05*i for i in range(1, 10)]
	rsi_period = [i for i in range(15)]

	data = load_data(DATA_FILE)[::-1]

	price = float(data[0][4])

	# print("Start!\nBtc Bal: {0: < 6} | Usd Bal: {1: < 6} | Total Btc: {2: < 6} | Total Usd: {3: < 6}".format(
	# 		round(btc_bal, 4), round(usd_bal, 4), 
	# 		round(btc_bal + usd_bal / price, 4),
	# 		round(btc_bal * price + usd_bal, 4)))

	for i, v in enumerate(rsi_period):
		btc_bal, usd_bal = run_simul(data, lin_buy_func, btc_bal=btc_bal, usd_bal=usd_bal,
			rsi_period=3, orders_per_rsi=3)

	# price = data[-1][4]
	# print("Endt\nBtc Bal: {0: < 6} | Usd Bal: {1: < 6} | Total Btc: {2: < 6} | Total Usd: {3: < 6}".format(
	# 		round(btc_bal, 4), round(usd_bal, 4), 
	# 		round(btc_bal + usd_bal / price, 4),
	# 		round(btc_bal * price + usd_bal, 4)))

	# print(datetime.fromtimestamp(data[-1][0]/1000))


if __name__ == '__main__':
	main()
