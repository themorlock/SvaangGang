
from datetime import datetime, timedelta

def calculate_rsi(prices: list, period: int) -> float:

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
