
from datetime import timedelta

def buy_func(base_size: int, hits: int):
	return base_size * (hits + 1)

def calc_rsi(data: list, period: int = 14) -> int:

	max_len = period if period < len(data) else len(data)

	prices = [i[4] for i in data]

	losses = []
	gains = []

	for i in range(1, max_len):
		change = prices[i] - prices[i-1]
		if change < 0:
			losses.append(abs(change))
		elif change > 0:
			gains.append(change)

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
