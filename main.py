
import logging.config
import logging
import asyncio
import yaml
import json
import time

from bitmex import bitmex

import trade_bot

BOT_CONFIG = "config.json"
LOG_CONFIG = "log_conf.yaml"


def get_config(file: str) -> dict:
	with open(file, "r") as f:
		return json.load(f)


def setup_logging(file: str, config: dict) -> None:
	with open(LOG_CONFIG, "r") as f:
		log_config = yaml.load(f)

		logging.config.dictConfig(log_config)

		level = logging.INFO if config["DEBUG"] else logging.DEBUG
		
		console_logger = logging.getLogger("main")
		console_logger.setLevel(level)

		bot_logger = logging.getLogger("bot")
		bot_logger.setLevel(level)

		console_logger.debug("Set up logging")


def main():

	config = get_config(BOT_CONFIG)
	setup_logging(LOG_CONFIG, config)

	logger = logging.getLogger("main")

	logger.info("Starting System")

	client = bitmex(test=config["TEST"], api_key=config["API_KEY"],
		api_secret=config["API_SECRET"])
	
	bot = trade_bot.Bot(config=config, logger=logging.getLogger("bot"),
		client=client)

	logger.info("Connected")
	logger.info("Starting")

	loop = asyncio.get_event_loop()
	future = asyncio.ensure_future(bot.start())
	loop.run_until_complete(future)
	loop.close()


if __name__ == "__main__":
	main()
