import asyncio

from bitmex import bitmex


class Bot:
    def __init__(self, config: dict, logger=None, client=None):
        self._config = config
        self._logger = logger
        self._api_secret = config["API_SECRET"]
        self._api_key = config["API_KEY"]
        self._symbol = config["SYMBOL"]
        self._rsi_interval = config["RSI_INTERVAL"]
        self._rsi_period = config["RSI_PERIOD"]
        self._orders = config["ORDERS_PER_RSI"]
        self._test = config["TEST"]
        self._sell_threshold = config["RSI_SELL"]
        self._buy_threshold = config["RSI_BUY"]
        self._rsi_midpoint = config["RSI_MIDPOINT"]
        self._rsi_midpoint_fluctuation_tolerance = config["RSI_MIDPOINT_FLUCTUATION_TOLERANCE"]
        self._rsi_midpoint_order_rate = config["RSI_MIDPOINT_ORDER_RATE"]
        self._rsi_sell_turnover_rate = config["RSI_SELL_TURNOVER_RATE"]
        self._rsi_buy_turnover_rate = config["RSI_BUY_TURNOVER_RATE"]
        self._contract_purchase_size = config["CONTRACT_PURCHASE_SIZE"]

        self._client = client if client else bitmex(test=self._test,
                                                    api_key=self._api_key, api_secret=self._api_secret)

    def _get_prices(self, count=1) -> float:
        return self._client.Quote.Quote_get(symbol=self._symbol, reverse=True, count=count).result()[0]

    def _calc_rsi(self):
        interval = self._rsi_interval
        quotes = self._get_prices(count=self._orders)[::-1]

        for quote in quotes:
            self._logger.debug((quote["timestamp"], quote["bidPrice"]))

        prices = [float(quote["bidPrice"]) for quote in quotes]

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
        previous_rsi = -1
        midway_traded = False
        order_book = []
        while True:
            rsi = self._calc_rsi()
            self._logger.info("RSI: {}".format(rsi))

            current_price = self._get_prices(count=1)[0]["bidPrice"]
            if not midway_traded and self._rsi_midpoint - self._rsi_midpoint_fluctuation_tolerance <= \
                    rsi <= self._rsi_midpoint + self._rsi_midpoint_fluctuation_tolerance:
                if self._sell_threshold <= previous_rsi <= 100:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "sell":
                            current_order_qty = order_book[i]["orderQty"] * self._rsi_midpoint_order_rate
                            order_book.pop(i)
                            break
                    self._logger.info("Buying Midway...")
                    order_data = {
                        "orderType": "buy",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }
                    self._client.Order.Order_new(symbol=self._symbol, orderQty=current_order_qty,
                                                 price=current_price).result()
                    order_book.append(order_data)
                    self._logger.info("Successfully Bought Midway!")
                    midway_traded = True
                elif 0 <= previous_rsi <= self._buy_threshold:
                    for i in range(0, len(order_book)):
                        if order_book[i]["orderType"] == "buy":
                            current_order_qty = order_book[i]["orderQty"] * self._rsi_midpoint_order_rate
                            order_book.pop(i)
                            break
                    self._logger.info("Selling Midway...")
                    order_data = {
                        "orderType": "sell",
                        "symbol": self._symbol,
                        "orderQty": current_order_qty,
                        "price": current_price
                    }
                    self._client.Order.Order_new(symbol=self._symbol, orderQty=-current_order_qty,
                                                 price=current_price).result()
                    order_book.append(order_data)
                    self._logger.info("Successfully Sold Midway!")
                    midway_traded = True
            elif rsi >= self._sell_threshold:
                current_order_qty = self._contract_purchase_size
                for i in range(0, len(order_book)):
                    if order_book[i]["orderType"] == "buy":
                        current_order_qty = order_book[i]["orderQty"] * self._rsi_buy_turnover_rate
                        order_book.pop(i)
                        break
                self._logger.info("Selling...")
                order_data = {
                    "orderType": "sell",
                    "symbol": self._symbol,
                    "orderQty": current_order_qty,
                    "price": current_price
                }
                self._client.Order.Order_new(symbol=self._symbol, orderQty=-current_order_qty,
                                             price=current_price).result()
                order_book.append(order_data)
                self._logger.info("Successfully Sold!")
                midway_traded = False
            elif rsi <= self._buy_threshold:
                current_order_qty = self._contract_purchase_size
                for i in range(0, len(order_book)):
                    if order_book[i]["orderType"] == "sell":
                        current_order_qty = order_book[i]["orderQty"] * self._rsi_sell_turnover_rate
                        order_book.pop(i)
                        break
                self._logger.info("Buying...")
                order_data = {
                    "orderType": "buy",
                    "symbol": self._symbol,
                    "orderQty": current_order_qty,
                    "price": current_price
                }
                self._client.Order.Order_new(symbol=self._symbol, orderQty=current_order_qty,
                                             price=current_price).result()
                order_book.append(order_data)
                self._logger.info("Successfully Bought!")
                midway_traded = False
            else:
                self._logger.info("Holding")

            previous_rsi = rsi
            await asyncio.sleep(int(self._rsi_period))
