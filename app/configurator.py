
import json

from indicators import rsi

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

		self.c_indicators = self.conf["Indicators"]
		self.bot = self.conf["Bot"]

		self.indicators = {
			"RSI": rsi.RSI,
		}
