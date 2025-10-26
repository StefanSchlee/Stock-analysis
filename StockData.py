from yahooquery import Ticker
import pandas as pd

class StockData:
    """
    Fetches all required stock data for a given symbol.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = Ticker(symbol)
        self.earnings_trend = None
        self.income_statement = None
        self.cash_flow = None
        self.history_5y = None
        self.history_20y = None
        self._fetch_all_data()
    
    def _fetch_all_data(self):
        # Earnings trend
        trend = self.ticker.earnings_trend
        self.earnings_trend = trend[self.symbol]['trend']

        # Income statement (EPS history)
        last_income = self.ticker.income_statement(trailing=False)
        self.income_statement = pd.DataFrame({
            'date': last_income['asOfDate'],
            'BasicEPS': last_income['BasicEPS']
        })

        # Cashflow
        last_cf = self.ticker.cash_flow()
        self.cash_flow = pd.Series(last_cf['CashFlowFromContinuingOperatingActivities'].array,
                                    pd.DatetimeIndex(last_cf['asOfDate']))

        # Chart history 5y
        hist5 = self.ticker.history(period='5y', interval='1d', adj_timezone=False)['close'][self.symbol]
        self.history_5y = pd.Series(hist5.values, pd.DatetimeIndex(hist5.index).tz_localize(None))

        # Chart history 20y
        hist20 = self.ticker.history(period='20y', interval='1d', adj_timezone=False)['close'][self.symbol]
        self.history_20y = pd.Series(hist20.values, pd.DatetimeIndex(hist20.index).tz_localize(None))
    
    def get_eps_estimates(self):
        """Extract current and next year EPS estimates and yearAgoEps"""
        current = next((p for p in self.earnings_trend if p['period'] == "0y"), None)
        next_y = next((p for p in self.earnings_trend if p['period'] == "+1y"), None)
        return current, next_y
