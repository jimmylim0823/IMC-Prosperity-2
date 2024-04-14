import math
import statistics
from typing import List, Dict, Tuple
from collections import deque, OrderedDict

from datamodel import *


class Strategy:
    """
    Base Class for Strategy Objects
    """
    def __init__(self, state: TradingState, product_config: dict):
        # product configuration
        self.symbol: Symbol = product_config['SYMBOL']
        self.product: Product = product_config['PRODUCT']
        self.position_limit: Position = product_config['POSITION_LIMIT']

        # extract information from TradingState
        self.timestamp = state.timestamp
        self.bids = OrderedDict(state.order_depths[self.symbol].buy_orders)
        self.asks = OrderedDict(state.order_depths[self.symbol].sell_orders)
        self.position = state.position.get(self.product, 0)
        self.best_bid = max(self.bids.keys())
        self.best_ask = min(self.asks.keys())

        # initialize variables for orders
        self.orders: List[Order] = []  # append orders for this product here
        self.expected_position = self.position  # expected position after market taking
        self.sum_buy_qty = 0  # check whether if buy order exceeds limit
        self.sum_sell_qty = 0  # check whether if buy order exceeds limit


class MarketMaking(Strategy):
    """
    Market making strategy with fair value.\n
    Sub-Strategy 1: Scratch by market taking for under / par valued orders\n
    Sub-Strategy 2: Stop loss if inventory piles over certain level\n
    Sub-Strategy 3: Market make around fair value with inventory management
    """
    def __init__(self, state: TradingState, product_config: dict, strategy_config: dict):
        super().__init__(state, product_config)

        # strategy configuration
        self.fair_value: float = strategy_config['FAIR_VALUE']  # initial or fixed fair value for market making
        self.sl_inventory: Position = strategy_config['SL_INVENTORY']  # acceptable inventory range
        self.sl_spread: int = strategy_config['SL_SPREAD']  # acceptable spread to take for stop loss
        self.mm_spread: int = strategy_config['MM_SPREAD']  # spread for market making
        self.order_skew: float = strategy_config['ORDER_SKEW']  # extra skewing order quantity when market making

    def scratch_under_valued(self):
        """
        Scratch any under-valued or par-valued orders by aggressing against bots
        """

        if -self.sl_inventory <= self.position <= self.sl_inventory:
            # use this strategy only when position is within stop loss inventory level
            if self.best_bid >= self.fair_value and len(self.bids) >= 2:
                # trade (sell) against bots trying to buy too expensive but not against worst bid
                order_quantity = min(max(-self.bids[self.best_bid],
                                         -self.position_limit - min(self.position, 0)), 0)
                self.orders.append(Order(self.symbol, self.best_bid, order_quantity))
                self.expected_position += order_quantity
                self.sum_sell_qty += order_quantity
                print(f"Scratch Sell {order_quantity} X @ {self.best_bid}")

            elif self.best_ask <= self.fair_value and len(self.asks) >= 2:
                # trade (buy) against bots trying to sell to cheap but not against worst ask
                order_quantity = max(min(-self.asks[self.best_ask],
                                         self.position_limit - max(self.position, 0)), 0)
                self.orders.append(Order(self.symbol, self.best_ask, order_quantity))
                self.expected_position += order_quantity
                self.sum_buy_qty += order_quantity
                print(f"Scratch Buy {order_quantity} X @ {self.best_ask}")

    def stop_loss(self):
        """
        Stop loss when inventory over acceptable level
        """
        if self.position > self.sl_inventory and self.best_bid >= self.fair_value - self.sl_spread:
            # stop loss sell not too cheap when in long position over acceptable inventory
            if len(self.bids) >= 2:
                # do not take worst bid which is also best bid
                order_quantity = max(-self.bids[self.best_bid], -self.position + self.sl_inventory)
                self.orders.append(Order(self.symbol, self.best_bid, order_quantity))
                self.expected_position += order_quantity
                self.sum_sell_qty += order_quantity
                print(f"Stop Loss Sell {order_quantity} X @ {self.best_bid}")

        elif self.position < -self.sl_inventory and self.best_ask <= self.fair_value + self.sl_spread:
            # stop loss buy not too expensive when in short position over acceptable inventory
            if len(self.asks) >= 2:
                # do not take worst ask which is also best ask
                order_quantity = min(-self.asks[self.best_ask], -self.position - self.sl_inventory)
                self.orders.append(Order(self.symbol, self.best_ask, order_quantity))
                self.expected_position += order_quantity
                self.sum_buy_qty += order_quantity
                print(f"Stop Loss Buy {order_quantity} X @ {self.best_ask}")

    def market_make(self):
        """
        Market make with fixed spread around fair value
        """
        # for limit consider position, expected position and single-sided aggregate
        bid_limit = max(min(self.position_limit,
                            self.position_limit - self.position,
                            self.position_limit - self.expected_position,
                            self.position_limit - self.sum_buy_qty - self.position), 0)
        ask_limit = min(max(-self.position_limit,
                            -self.position_limit - self.position,
                            -self.position_limit - self.expected_position,
                            -self.position_limit - self.sum_sell_qty - self.position), 0)

        # natural order skew due to limit + extra skewing to prevent further adverse selection
        bid_skew = math.ceil(self.order_skew * max(self.expected_position, 0))
        ask_skew = math.floor(self.order_skew * min(self.expected_position, 0))
        bid_quantity = min(max(bid_limit - bid_skew, 0), bid_limit)
        ask_quantity = max(min(ask_limit - ask_skew, 0), ask_limit)

        # determine price for market making using fair value as reserve price
        bid_price = math.ceil(self.fair_value - self.mm_spread)
        ask_price = math.floor(self.fair_value + self.mm_spread)
        self.orders.append(Order(self.symbol, bid_price, bid_quantity))
        self.orders.append(Order(self.symbol, ask_price, ask_quantity))
        print(f"Market Make Bid {bid_quantity} X @ {bid_price} Ask {ask_quantity} X @ {ask_price}")

    def aggregate_orders(self) -> List[Order]:
        """
        Aggregate all orders from all sub strategies under market making

        :rtype: List[Order]
        :return: List of orders generated for product
        """

        print(f"{self.symbol} Position {self.position}")
        self.scratch_under_valued()
        self.stop_loss()
        self.market_make()
        return self.orders


class LinearRegressionMM(MarketMaking):
    def __init__(self, state: TradingState,
                 product_config: dict, strategy_config: dict, regression_config: dict):
        super().__init__(state, product_config, strategy_config)
        self.min_window_size = regression_config['MIN_WINDOW_SIZE']
        self.max_window_size = regression_config['MAX_WINDOW_SIZE']
        self.predict_shift = regression_config['PREDICT_SHIFT']

        # volume weighted average price (vwap) for bid, ask, and mid for de-noising
        self.bid_vwap = sum(p * q for p, q in self.bids.items()) / sum(self.bids.values())
        self.ask_vwap = sum(p * q for p, q in self.asks.items()) / sum(self.asks.values())
        self.mid_vwap = (self.bid_vwap + self.ask_vwap) / 2

    def predict_price(self, price_history: deque):
        """
        Predict price value after n timestamp shift with linear regression and update fair value

        :param price_history: (deque) Array of historical prices
        """
        n = len(price_history)
        if n >= self.min_window_size:
            t = int(self.timestamp / 100)
            xs = [100 * i for i in range(t - n + 1, t + 1)]
            ys = list(price_history)
            slope, intercept = statistics.linear_regression(xs, ys)
            y_hat = slope * (self.timestamp + 100 * self.predict_shift) + intercept
            self.fair_value = y_hat
        else:
            self.fair_value = self.mid_vwap


class OTCArbitrage(Strategy):
    """
    Arbitrage Between OTC and Exchange comparing with estimated fair value
    """
    def __init__(self, state: TradingState,
                 product_config: dict, strategy_config: dict):
        super().__init__(state, product_config)
        self.unit_cost_storing = product_config['COST_STORING']

        # extract information from conversion observation
        self.observation = state.observations.conversionObservations[self.symbol]
        self.otc_bid = self.observation.bidPrice
        self.otc_ask = self.observation.askPrice
        self.otc_mid = (self.otc_bid + self.otc_ask) / 2
        self.cost_import = self.observation.transportFees + self.observation.importTariff
        self.cost_export = self.observation.transportFees + self.observation.exportTariff
        self.sunlight = self.observation.sunlight
        self.humidity = self.observation.humidity

        # define variables related to conversion
        self.fair_value = self.otc_mid  # initialize
        self.conversions = 0  # reset every timestamp

        # strategy configuration
        self.expected_storage_time = strategy_config['EXP_STORAGE_TIME']
        self.effective_cost_export = self.cost_export + self.expected_storage_time * self.unit_cost_storing
        self.min_edge = strategy_config['MIN_EDGE']
        self.mm_edge = strategy_config['MM_EDGE']

    def calc_fair_value(self):
        self.fair_value = self.otc_mid  # temporary

    def arbitrage_exchange_enter(self):
        """
        Long Arbitrage: take exchange best ask (buy) then take next otc bid (sell)\n
        Short Arbitrage: take exchange best bid (sell) then take next otc ask (buy)\n
        Note you pay export storing cost for long arb but only import cost for short arb
        """
        # calculate effective import and export cost then get arbitrage edge of each side
        long_arb_edge = self.otc_bid - self.best_ask - self.effective_cost_export
        short_arb_edge = self.best_bid - self.otc_ask - self.cost_import

        edges = {"Long": long_arb_edge, "Short": short_arb_edge}
        max_key = max(edges, key=lambda k: edges[k])  # choose best side
        if max_key == "Long" and edges[max_key] >= self.min_edge:
            for price, quantity in self.asks.items():
                if self.otc_bid - price - self.effective_cost_export >= self.min_edge:
                    order_quantity = max(min(-quantity,
                                             self.position_limit - max(self.expected_position, 0)), 0)
                    self.orders.append(Order(self.symbol, price, order_quantity))
                    print(f"{max_key} Arbitrage {order_quantity} X @ {self.best_ask}")
                    self.expected_position += order_quantity
                    self.sum_buy_qty += order_quantity
                else:
                    break
        elif max_key == "Short" and edges[max_key] >= self.min_edge:
            for price, quantity in self.bids.items():
                if price - self.otc_ask - self.cost_import >= self.min_edge:
                    order_quantity = min(max(-self.bids[self.best_bid],
                                             -self.position_limit - min(self.expected_position, 0)), 0)
                    self.orders.append(Order(self.symbol, self.best_bid, order_quantity))
                    print(f"{max_key} Arbitrage Enter {order_quantity} X @ {self.best_bid}")
                    self.expected_position += order_quantity
                    self.sum_sell_qty += order_quantity
                else:
                    break

    def arbitrage_otc_exit(self):
        """
        Exit position from arbitrage strategy by converting position in otc
        """
        exit_quantity = -self.position  # need to change quantity if other strategy added
        self.conversions += exit_quantity
        if exit_quantity > 0:
            print(f"Short Arbitrage Exit {exit_quantity} X @ {self.otc_ask}")
        elif exit_quantity < 0:
            print(f"Long Arbitrage Exit {exit_quantity} X @ {self.otc_bid}")

    def market_make(self):
        """
        Bid low enough to take bid (sell) arbitrage-freely in otc considering cost\n
        Ask high enough to take ask (buy) arbitrage-freely in otc considering cost
        """
        # for limit consider position, expected position and single-sided aggregate
        bid_quantity = max(min(self.position_limit,
                               self.position_limit - self.position,
                               self.position_limit - self.expected_position,
                               self.position_limit - self.sum_buy_qty - self.position), 0)
        ask_quantity = min(max(-self.position_limit,
                               -self.position_limit - self.position,
                               -self.position_limit - self.expected_position,
                               -self.position_limit - self.sum_sell_qty - self.position), 0)

        # determine price for market making by adding edge to arbitrage free price
        pricing_shift = self.fair_value - self.otc_mid
        bid_arb_free = self.otc_bid - self.effective_cost_export
        ask_arb_free = self.otc_ask + self.cost_import
        bid_price = math.floor(bid_arb_free - self.mm_edge + pricing_shift)
        ask_price = math.ceil(ask_arb_free + self.mm_edge + pricing_shift)
        self.orders.append(Order(self.symbol, bid_price, bid_quantity))
        self.orders.append(Order(self.symbol, ask_price, ask_quantity))
        print(f"Market Make Bid {bid_quantity} X @ {bid_price} Ask {ask_quantity} X @ {ask_price}")

    def aggregate_orders_conversions(self) -> Tuple[List[Order], int]:
        """
        Aggregate all orders from all sub strategies under OTC Arbitrage

        :rtype: List[Order]
        :return: List of orders generated for product
        """
        print(f"{self.symbol} Position {self.position}")
        self.arbitrage_exchange_enter()
        self.arbitrage_otc_exit()
        self.market_make()
        return self.orders, self.conversions


class Trader:
    data = {'STARFRUIT': deque()}
    config = {'PRODUCT': {'AMETHYSTS': {'SYMBOL': 'AMETHYSTS',
                                        'PRODUCT': 'AMETHYSTS',
                                        'POSITION_LIMIT': 20},
                          'STARFRUIT': {'SYMBOL': 'STARFRUIT',
                                        'PRODUCT': 'STARFRUIT',
                                        'POSITION_LIMIT': 20},
                          'ORCHIDS': {'SYMBOL': 'ORCHIDS',
                                      'PRODUCT': 'ORCHIDS',
                                      'POSITION_LIMIT': 100,
                                      'COST_STORING': 0.1}},
              'STRATEGY': {'AMETHYSTS': {'FAIR_VALUE': 10000.0,
                                         'SL_INVENTORY': 20,
                                         'SL_SPREAD': 1,
                                         'MM_SPREAD': 2,
                                         'ORDER_SKEW': 1.0},
                           'STARFRUIT': {'FAIR_VALUE': 5000.0,
                                         'SL_INVENTORY': 10,
                                         'SL_SPREAD': 1,
                                         'MM_SPREAD': 2,
                                         'ORDER_SKEW': 1.0},
                           'ORCHIDS': {'EXP_STORAGE_TIME': 1,
                                       'MIN_EDGE': 1.5,
                                       'MM_EDGE': 1.6}},
              'REGRESSION': {'STARFRUIT': {'MIN_WINDOW_SIZE': 5,
                                           'MAX_WINDOW_SIZE': 10,
                                           'PREDICT_SHIFT': 1}}}

    def data_starfruit(self, strategy: LinearRegressionMM):
        """
        Store new mid vwap data for Starfruit to class variable as queue

        :param strategy: (LinearRegressionMM) Strategy class for Starfruit
        """
        mid_vwap = strategy.mid_vwap
        while len(self.data[strategy.symbol]) >= strategy.max_window_size:
            self.data[strategy.symbol].popleft()
        self.data[strategy.symbol].append(mid_vwap)

    def run(self, state: TradingState):
        result = {}
        conversions = 0
        traderData = "SAMPLE"

        # Round 1: AMETHYSTS and STARFRUIT (Market Making)
        # Symbol 1: AMETHYSTS (Fixed Fair Value Market Making)
        strategy_amethysts = MarketMaking(state,
                                          self.config['PRODUCT']['AMETHYSTS'],
                                          self.config['STRATEGY']['AMETHYSTS'])
        result["AMETHYSTS"] = strategy_amethysts.aggregate_orders()

        # Symbol 2: STARFRUIT (Linear Regression Market Making)
        strategy_starfruit = LinearRegressionMM(state,
                                                self.config['PRODUCT']['STARFRUIT'],
                                                self.config['STRATEGY']['STARFRUIT'],
                                                self.config['REGRESSION']['STARFRUIT'])
        self.data_starfruit(strategy_starfruit)  # update data
        strategy_starfruit.predict_price(self.data['STARFRUIT'])  # update fair value
        result["STARFRUIT"] = strategy_starfruit.aggregate_orders()

        # Round 2: ORCHIDS (OTC-Exchange Arbitrage)
        strategy_orchids = OTCArbitrage(state,
                                        self.config['PRODUCT']['ORCHIDS'],
                                        self.config['STRATEGY']['ORCHIDS'])
        result["ORCHIDS"], conversions = strategy_orchids.aggregate_orders_conversions()

        return result, conversions, traderData
