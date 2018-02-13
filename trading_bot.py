
from datetime import datetime, timedelta
import asyncio

from ccxt import bitmex


class Bot:
    def __init__(self, config: dict, logger=None, client=None):
        self._config = config
        self._logger = logger

        self._symbol = config["symbol"]

        self._timeframe = config["timeframe"]
        self._rsi_period = config["rsi_period"]
        self._orders = config["orders_per_rsi"]

        self._sell_threshold = config["RSI_SELL"]
        self._buy_threshold = config["RSI_BUY"]

        self._rsi_trade_at_midpoint = config["RSI_TRADE_AT_MIDPOINT"]
        self._rsi_midpoint_fluctuation_tolerance = config["RSI_MIDPOINT_FLUCTUATION_TOLERANCE"]
        self._rsi_midpoint_order_rate = config["RSI_MIDPOINT_ORDER_RATE"]
        self._rsi_sell_turnover_rate = config["RSI_SELL_TURNOVER_RATE"]
        self._contract_purchase_size = config["CONTRACT_PURCHASE_SIZE"]
        self._rsi_buy_turnover_rate = config["RSI_BUY_TURNOVER_RATE"]
        self._rsi_previous_hits = config["RSI_PREVIOUS_HITS"]
        self._rsi_midpoint = config["RSI_MIDPOINT"]

        self._update_interval = config["update_interval"]

        if client:
            self._client = client

        else: 
            self._client = bitmex({
                "test": config["test"],
                "apiKey": config["key"],
                "secret": config["secret"]
                })


    def _get_timestamp(self, count) -> int:
        if self._timeframe == "1m":
            t = datetime.now() - timedelta(minutes=count)
            return t.timestamp() * 1000

        elif self._timeframe == "3m":
            print(3*count+1)
            t = datetime.now() - timedelta(minutes=3*count)
            return t.timestamp() * 1000

        elif self._timeframe == "5m":
            t = datetime.now() - timedelta(minutes=5*count)
            return t.timestamp() * 1000

        elif self._timeframe == "1h":
            t = datetime.now() - timedelta(hours=count)
            return (datetime.now() - timedelta(hours=count)).timestamp() * 1000

        t = datetime.now() - timedelta(days=count)
        return t.timestamp() * 1000


    def _curr_price(self) -> float:
        return self._cliet.fetch_ticker("BTC/USD")


    def _get_history(self, count=1) -> float:
        last = self._get_timestamp(count)

        t = self._timeframe
        t = t if t != "3m" else "1m"
        data = self._client.fetch_ohlcv("BTC/USD", timeframe=t, since=last)[::-1]

        if self._timeframe == "3m":
            return data[::2]

        return data 


    def _calc_rsi(self):
        interval = self._rsi_period
        hist = self._get_history(count=self._orders)

        prices = []

        for order in hist:
            p = order[4]
            self._logger.debug((datetime.utcfromtimestamp(order[0]/1000), p))
            prices.append(p)

        print(len(prices))

        max_len = interval if interval < len(prices) else len(prices)

        losses = []
        gains = []

        for i in range(1, max_len):
            change = prices[i] - prices[i-1]
            if change < 0:
                losses.append(abs(change))
            elif change > 0:
                gains.append(change)

        avg_loss = sum(losses) / interval
        avg_gain = sum(gains) / interval

        for i in range(interval, len(prices)):
            change = prices[i] - prices[i - 1]
            loss = abs(change) if change < 0 else 0
            gain = change if change > 0 else 0

            avg_gain = (avg_gain * (interval - 1) + gain) / interval
            avg_loss = (avg_loss * (interval - 1) + gain) / interval

        if avg_loss == 0:
            return 100
        elif avg_gain == 0:
            return 0

        rs = avg_gain / avg_loss
        rsi = round(100 - (100 / (1 + rs)), 2)

        return rsi


    async def start(self):
        previous_rsis = [-1]
        midway_traded = False
        order_book = []
        while True:

            rsi = self._calc_rsi()
            self._logger.info("RSI: {}".format(rsi))

            current_price = self._curr_price

            if self._rsi_trade_at_midpoint and not midway_traded and self._rsi_midpoint - self._rsi_midpoint_fluctuation_tolerance <= \
                    rsi <= self._rsi_midpoint + self._rsi_midpoint_fluctuation_tolerance:

                if all(self._sell_threshold <= previous_rsi <= 100 for previous_rsi in previous_rsis):
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_midpoint_order_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Buying Midway...")

                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Bought Midway!")
                    midway_traded = True

                elif all(0 <= previous_rsi <= self._buy_threshold for previous_rsi in previous_rsis):
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_midpoint_order_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Selling Midway...")

                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_sell_order(symbol=self._symbol, amount=-current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold Midway!")
                    midway_traded = True

            elif rsi >= self._sell_threshold:
                try:
                    current_order_qty = self._contract_purchase_size
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_buy_turnover_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Selling...")
                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_sell_order(symbol=self._symbol, amount=-current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold!")
                    midway_traded = False

                except:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = int(order_book[i]["orderQty"])
                            order_book.pop(i)
                            break
                    self._logger.info("Selling...")
                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_sell_order(symbol=self._symbol, amount=-current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Sold!")
                    midway_traded = False

            elif rsi <= self._buy_threshold:
                try:
                    current_order_qty = self._contract_purchase_size
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = int(order_book[i]["orderQty"] * self._rsi_sell_turnover_rate)
                            order_book.pop(i)
                            break

                    self._logger.info("Buying...")

                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)
                    self._logger.info("Successfully Bought!")
                    midway_traded = False

                except:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = int(order_book[i]["orderQty"])
                            order_book.pop(i)
                            break
                    self._logger.info("Buying...")

                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }

                    self._client.create_market_buy_order(symbol=self._symbol, amount=current_order_qty)

                    order_book.append(order_data)

                    self._logger.info("Successfully Bought!")

                    midway_traded = False
            else:
                self._logger.info("Holding")

            if len(previous_rsis) == self._rsi_previous_hits:
                previous_rsis.pop(0)

            previous_rsis.append(rsi)

            self._logger.info("Curr Balance {}".format(
                self._client.fetch_balance()["total"]["BTC"]))

            await asyncio.sleep(int(self._update_interval * 60))
