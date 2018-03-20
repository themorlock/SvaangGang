
import logging
import asyncio
import json
import sys

import ccxt.async as ccxt

sys.path.append("app")
sys.path.append("app/indicators")
from app import trading_bot, configurator

BOT_CONFIG = "config.json"


def setup_logging(config: dict) -> None:
	logger = logging.getLogger()

	level = logging.DEBUG if config["debug"] else logging.INFO

	f_handler = logging.FileHandler(filename="svaang.log", encoding="utf-8", mode="w")
	cl_handler = logging.StreamHandler()

	dt_fmt = "%Y-%m-%d %H:%M:%S"
	fmt = logging.Formatter("[{asctime}] [{levelname:<6}] {name}: {message}", 
		dt_fmt, style="{")

	cl_handler.setFormatter(fmt)
	f_handler.setFormatter(fmt)

	logger.addHandler(cl_handler)
	logger.addHandler(f_handler)
	logger.setLevel(level)


def get_exchange(config: dict) -> ccxt.Exchange:
	if config["test"]:
		client = ccxt.bitmex({
			"urls": {
				"api": "https://testnet.bitmex.com",
				"test": "https://www.bitmex.com"
			},
			"apiKey": config["key"],
			"secret": config["secret"]
			})
	else:
		client = ccxt.bitmex({
			"apiKey": config["key"],
			"secret": config["secret"]
			})

	return client


def main():
	config = configurator.Config(file=BOT_CONFIG)
	setup_conf = config.conf

	setup_logging(setup_conf)

	logger = logging.getLogger()
	logger.info("Starting System...")

	exchange = get_exchange(setup_conf)

	logger.info("Connected To Servers!!!")
	bot = trading_bot.Bot(config, logger, exchange)

	logger.info("Starting")

	loop = asyncio.get_event_loop()
	loop.run_until_complete(bot.start())
	loop.close()


if __name__ == "__main__":
	main() 
	