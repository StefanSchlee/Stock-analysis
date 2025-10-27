from yahooquery import Ticker
import pandas as pd


class StockData:
    """
    Fetches all required stock data for a given symbol.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = Ticker(symbol)
        self.number_of_shares = None
        self.earnings_trend = None
        self.income_statement = None
        self.cash_flow = None
        self.cash_flow_per_share = None
        self.history_5y = None
        self.history_20y = None
        self._fetch_all_data()

    def _fetch_all_data(self):
        # Earnings trend
        trend = self.ticker.earnings_trend
        self.earnings_trend = trend[self.symbol]["trend"]

        # Income statement (EPS history)
        last_income = self.ticker.income_statement(trailing=False)
        self.income_statement = pd.DataFrame(
            {
                "date": last_income["asOfDate"],
                "BasicEPS": last_income["BasicEPS"],
            }
        )

        self.number_of_shares = pd.Series(
            last_income["BasicAverageShares"].array,
            pd.DatetimeIndex(last_income["asOfDate"]),
        )

        # Cashflow
        last_cf = self.ticker.cash_flow(trailing=False)
        self.cash_flow = pd.Series(
            last_cf["OperatingCashFlow"].array, pd.DatetimeIndex(last_cf["asOfDate"])
        )

        self.cash_flow_per_share = pd.Series(
            self.cash_flow.array / self.number_of_shares.array, self.cash_flow.index
        )

        # Chart history 20y (omit latest value, as this is datetime not date)
        hist20 = self.ticker.history(period="20y", interval="1d", adj_timezone=False)[
            "close"
        ][self.symbol]
        self.history_20y = pd.Series(
            hist20.values[:-1], pd.DatetimeIndex(hist20.index[:-1]).tz_localize(None)
        )

        # Chart history 5y
        five_years_ago = self.history_20y.index[-1] - pd.Timedelta(days=365 * 5)
        self.history_5y = self.history_20y.truncate(before=five_years_ago)

    def get_eps_estimates(self):
        """Extract current and next year EPS estimates and yearAgoEps"""
        current = next((p for p in self.earnings_trend if p["period"] == "0y"), None)
        next_y = next((p for p in self.earnings_trend if p["period"] == "+1y"), None)
        return current, next_y
