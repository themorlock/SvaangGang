
from datetime import datetime
import math
import json
import csv
import sys

sys.path.append("../helpers")


DATA_FILE = "data.json"

def load_data(file):
	with open(file, "r") as f:
		return json.load(f)


def lin_buy_func(base_size: int, hits: int, k: int = 1.61):
	return base_size * (k*hits + 1)


def sig_buy_func(max_balance: float, hits: int, k: int = 1):
	return max_balance / (1 + math.exp(-(k*hits - 5)))
						  

def calc_rsi(data: list, period: int = 14) -> int:

	max_len = period if period < len(data) else len(data)

	prices = [i[4] for i in data]

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
			print(e + " " + prices)


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


def run_simul(data: list, buy_func, btc_bal: float = 0.1, usd_bal: float = 100,
		order_size: float = 0.1, rsi_sell: int = 70,
		rsi_buy: int = 30, rsi_period: int = 14,
		orders_per_rsi: int = 14, return_hist: bool = False):

	sell_hits = 0
	buy_hits = 0

	if return_hist:
		hist = []

	for i in range(orders_per_rsi, len(data)):
		rsi = calc_rsi(data[i - orders_per_rsi:i], rsi_period)

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
			hist.append({
				"timestamp": data[i][0]/1000,
				"usd_bal": usd_bal, 
				"btc_bal": btc_bal,
				"total_btc_bal": btc_bal + (usd_bal / price),
				"total_usd_bal": usd_bal + (btc_bal * price),
				"btc_price": price 
				})

	if return_hist:
		return (btc_bal, usd_bal, hist)

	return (btc_bal, usd_bal)
			  

def main():
	init_btc_bal = 0.1
	init_usd_bal = 100

	size = 0.1 # percent

	sell = 70
	buy = 30

	# stuff to test
	rsi_periods = [14]
	rsi_data_size = [1000]
	order_sizes = [0.12]

	data = load_data(DATA_FILE)[::-1]

	price = float(data[0][4])

	print("Start!\nBtc Bal: {0: < 10} | Usd Bal: {1: < 10} \
		| Total Btc: {2: < 10} | Total Usd: {3: < 10}".format(
		round(init_btc_bal, 4), round(init_usd_bal, 4), 
		round(init_btc_bal + init_usd_bal / price, 4),
		round(init_btc_bal * price + init_usd_bal, 4)))

	price = float(data[-1][4])

	for period in rsi_periods:
		for order_size in order_sizes:
			for data_size in rsi_data_size:

				btc_bal, usd_bal, hist = run_simul(data, lin_buy_func, 
					btc_bal=init_btc_bal, usd_bal=init_usd_bal, 
					rsi_period=period, orders_per_rsi=data_size, 
					return_hist=True)

				total_btc_bal = round(btc_bal + usd_bal / price, 6)
				total_usd_bal = round(btc_bal * price + usd_bal, 2)
				gain = round(total_btc_bal / init_btc_bal, 2)

				print("\nRSI Period: {0} Order Size: {1} RSI Data Size {2}"\
					.format(period, order_size, data_size))

				text = "End\nBtc Bal: {0: < 6} | Usd Bal: {1: < 6} | Total Btc: {2: < 8} | Total Usd: {3: < 6} | Gain: {4: < 6}"
				print(text.format(
					round(btc_bal, 4), round(usd_bal, 4),
					total_btc_bal, total_usd_bal, gain)
				)


if __name__ == '__main__':
	main()
