from datamodel import OrderDepth, TradingState, Position, Order
from typing import List


class StrategyAmethysts:
    SYMBOL = "AMETHYSTS"
    FAIR_VALUE = 10000
    POSITION_LIMIT = 20

    def __init__(self, order_depth: OrderDepth, position: Position):
        self.bids = order_depth.buy_orders
        self.asks = order_depth.sell_orders
        self.position = position

    def scratch_under_valued(self):
        # scratch any par or under-valued order
        orders: List[Order] = []
        
        for bid_price, bid_amount in enumerate(self.bids):
            if bid_price >= self.FAIR_VALUE:
                orders.append(Order(self.SYMBOL, bid_price, -bid_amount))
        for ask_price, ask_amount in enumerate(self.asks):
            if ask_price >= self.FAIR_VALUE:
                orders.append(Order(self.SYMBOL, ask_price, -ask_amount))
        return orders


class Trader:
    @staticmethod
    def run(state: TradingState):
        result = {}
        conversions = 0
        traderData = "SAMPLE"

        return result, conversions, traderData
