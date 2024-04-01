from datamodel import OrderDepth, TradingState, Order


class StrategyAmethysts:
    FAIR_VALUE = 10000
    POSITION_LIMIT = 20

    def __init__(self, order_depth: OrderDepth):
        self.bids = order_depth.buy_orders
        self.asks = order_depth.sell_orders



class Trader:
    @staticmethod
    def run(state: TradingState):
        result = {}
        conversions = 0
        traderData = "SAMPLE"

        return result, conversions, traderData
