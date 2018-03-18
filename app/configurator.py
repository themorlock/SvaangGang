
import json

from indicators import *

def get_config(file: str) -> dict:
	with open(file, "r") as f:
		return json.load(f)

class Config:
	def __init__(self, config: dict=None, file: str=None):
		if file:
			cfg = get_config(file)

		if config:
			config.update(cfg)
		else:
			config = cfg

		self.conf = config

		self.indicator = self.conf["Indicators"]
		self.rsi = self.indicator_config["RSI"]
		self.bot = self.conf["Bot"]

		self.indicators = {
			"RSI": rsi.RSI,
		}

	def get_indicator(self):
		return self.indicators[self.indicator]
