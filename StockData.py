from yahooquery import Ticker
import finqual as fq
import pandas as pd
from datetime import datetime


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
        self.fq_balance_df = None
        self.fq_income_df = None
        self.fq_cashflow_df = None
        self.fq_eps = None
        self._fetch_all_data()

    def _fetch_all_data(self):
        ## get finqual dataframes
        print("Getting finqual data ...")
        fq_obj = fq.Finqual(self.symbol)

        # ask a 30 year timeframe
        current_year = datetime.now().year
        start_year = current_year - 30
        self.fq_balance_df = (
            fq_obj.balance_sheet_period(start_year, current_year)
            .to_pandas()
            .set_index(self.symbol)
            .T
        )
        self.fq_balance_df.index = pd.to_datetime(
            self.fq_balance_df.index.astype(str) + "-12-31"
        )
        self.fq_income_df = (
            fq_obj.income_stmt_period(start_year, current_year)
            .to_pandas()
            .set_index(self.symbol)
            .T
        )
        self.fq_income_df.index = pd.to_datetime(
            self.fq_income_df.index.astype(str) + "-12-31"
        )
        self.fq_cashflow_df = (
            fq_obj.cash_flow_period(start_year, current_year)
            .to_pandas()
            .set_index(self.symbol)
            .T
        )
        self.fq_cashflow_df.index = pd.to_datetime(
            self.fq_cashflow_df.index.astype(str) + "-12-31"
        )
        print("Getting finqual data ... done")

        # finqual eps
        fq_net_income = self.fq_income_df["Net Income"]
        fq_net_income = fq_net_income[fq_net_income > 0]

        fq_shares = self.fq_balance_df["Shares Outstanding"]
        fq_shares = fq_shares[fq_shares > 0]

        common_idx = fq_net_income.index.intersection(fq_shares.index)
        self.fq_eps = fq_net_income[common_idx] / fq_shares[common_idx]

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
