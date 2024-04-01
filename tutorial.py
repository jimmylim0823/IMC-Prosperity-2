from datamodel import OrderDepth, TradingState, Position, Order
from typing import List


class StrategyAmethysts:
    """
    Market making strategy for Amethysts with fixed fair value.
    Sub-Strategy 1: Scratch by market taking for free lunch
    Sub-Strategy 2: Stop loss if inventory piles over certain level
    Sub-Strategy 3: Market Make
    """

    SYMBOL = "AMETHYSTS"
    FAIR_VALUE = 10000
    POSITION_LIMIT = 20
    SL_INVENTORY = 15  # acceptable inventory range
    SL_SPREAD = 2  # stop loss within this spread
    MM_SPREAD = 3  # market make with spread no smaller than this

    def __init__(self, order_depth: OrderDepth, position: Position):
        self.bids = order_depth.buy_orders
        self.asks = order_depth.sell_orders
        self.position = position
        self.best_bid = max(self.bids.keys())
        self.best_ask = min(self.asks.keys())
        self.expected_position = self.position  # expected position if all orders are filled
        self.orders: List[Order] = []

    def scratch_under_valued(self):
        """
        Scratch any under-valued or par-valued orders by aggressing against bots
        """
        if self.position <= 0 and self.best_bid >= self.FAIR_VALUE:
            # trade (sell) against bots trying to buy too expensive
            for price, quantity in enumerate(self.bids):
                if price >= self.FAIR_VALUE and self.expected_position < -self.POSITION_LIMIT:
                    order_quantity = min(max(-quantity, -self.POSITION_LIMIT - self.expected_position), 0)
                    self.orders.append(Order(self.SYMBOL, price, order_quantity))
                    self.expected_position += order_quantity
        elif self.position >= 0 and self.best_ask <= self.FAIR_VALUE:
            # trade (buy) against bots trying to sell to cheap
            for price, quantity in enumerate(self.asks):
                if price >= self.FAIR_VALUE and self.expected_position > self.POSITION_LIMIT:
                    order_quantity = max(min(-quantity, self.POSITION_LIMIT - self.expected_position), 0)
                    self.orders.append(Order(self.SYMBOL, price, order_quantity))
                    self.expected_position += order_quantity

    def stop_loss(self):
        """
        Stop loss when inventory over acceptable level
        """
        if self.position > self.SL_INVENTORY and self.best_bid >= self.FAIR_VALUE - self.SL_SPREAD:
            # stop loss sell while in long position over acceptable inventory
            for price, quantity in enumerate(self.bids):
                if price >= self.FAIR_VALUE - self.SL_SPREAD and self.expected_position < -self.POSITION_LIMIT:
                    order_quantity = min(max(-quantity, -self.POSITION_LIMIT - self.expected_position), 0)
                    self.orders.append(Order(self.SYMBOL, price, order_quantity))
                    self.expected_position += order_quantity
        elif self.position < -self.SL_INVENTORY and self.best_ask <= self.FAIR_VALUE + self.SL_SPREAD:
            # stop loss buy while in short position over acceptable inventory
            for price, quantity in enumerate(self.asks):
                if price <= self.FAIR_VALUE + self.SL_SPREAD and self.expected_position > -self.POSITION_LIMIT:
                    order_quantity = max(min(-quantity, self.POSITION_LIMIT - self.expected_position), 0)
                    self.orders.append(Order(self.SYMBOL, price, order_quantity))
                    self.expected_position += order_quantity

    def market_make(self):
        """
        Market make with fixed spread around fair value
        """
        bid_quantity = max(self.POSITION_LIMIT - self.expected_position, 0)
        ask_quantity = min(-self.POSITION_LIMIT - self.expected_position, 0)
        bid_price = self.FAIR_VALUE - self.MM_SPREAD
        ask_price = self.FAIR_VALUE + self.MM_SPREAD
        self.orders.append(Order(self.SYMBOL, bid_price, bid_quantity))
        self.orders.append(Order(self.SYMBOL, ask_price, ask_quantity))

    def aggregate_orders(self) -> List[Order]:
        """
        Aggregate all orders from various strategies

        :rtype: List[Order]
        :return: List of orders generated for product Amethysts
        """
        self.scratch_under_valued()
        self.stop_loss()
        self.market_make()
        return self.orders


class Trader:
    @staticmethod
    def run(state: TradingState):
        result = {}
        conversions = 0
        traderData = "SAMPLE"

        # Symbol 1: AMETHYSTS (Fixed Fair Value Market Making)
        strategy_amethysts = StrategyAmethysts(state.order_depths["AMETHYSTS"], state.position["AMETHYSTS"])
        result["AMETHYSTS"] = strategy_amethysts.aggregate_orders()

        return result, conversions, traderData
