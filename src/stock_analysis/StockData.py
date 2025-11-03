from yahooquery import Ticker
import finqual as fq
import pandas as pd
from datetime import datetime


class StockData:
    """
    Fetches all required stock data for a given symbol.
    """

    symbol: str
    ticker: Ticker
    fq_balance_df: pd.DataFrame
    fq_income_df: pd.DataFrame
    fq_cashflow_df: pd.DataFrame
    fq_eps: pd.Series
    yh_current_year_estimates: dict
    yh_next_year_estimates: dict

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = Ticker(symbol)
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

        ## get yahoo data
        # Income statement (EPS history)
        self.income_statement = self.ticker.income_statement(trailing=False)

        # get earnings release date from yahoo, and adapt finqual dateindex accordingly
        earnings_date = self.income_statement["asOfDate"].iloc[0]
        self.fq_balance_df.index = self.fq_balance_df.index.map(
            lambda d: d.replace(month=earnings_date.month, day=earnings_date.day)
        )
        self.fq_income_df.index = self.fq_income_df.index.map(
            lambda d: d.replace(month=earnings_date.month, day=earnings_date.day)
        )
        self.fq_cashflow_df.index = self.fq_cashflow_df.index.map(
            lambda d: d.replace(month=earnings_date.month, day=earnings_date.day)
        )

        # finqual eps
        fq_net_income = self.fq_income_df["Net Income"]
        fq_net_income = fq_net_income[fq_net_income > 0]
        if len(fq_net_income) == 0:
            raise ValueError("No net income data availabe!")

        fq_shares = self.fq_balance_df["Shares Outstanding"]
        fq_shares = fq_shares[fq_shares > 0]
        if len(fq_shares) == 0:
            raise ValueError("No number of shares data available!")

        common_idx = fq_net_income.index.intersection(fq_shares.index)
        self.fq_eps = fq_net_income[common_idx] / fq_shares[common_idx]

        ## get future estimates from yahoo
        trend = self.ticker.earnings_trend[self.symbol]["trend"]
        self.yh_current_year_estimates, self.yh_next_year_estimates = (
            self.get_eps_estimates(trend)
        )

        # compute correction factor for the estimated eps
        EPScorrectionFactor = (
            self.fq_eps.iloc[0]
            / self.yh_current_year_estimates["earningsEstimate"]["yearAgoEps"]
        )
        print(f"EPS Correction factor: {EPScorrectionFactor}")

        # add estimated eps to eps array
        estimated_eps_series = pd.Series(
            [
                self.yh_next_year_estimates["earningsEstimate"]["avg"],
                self.yh_current_year_estimates["earningsEstimate"]["avg"],
            ],
            pd.DatetimeIndex(
                [
                    self.yh_next_year_estimates["endDate"],
                    self.yh_current_year_estimates["endDate"],
                ]
            ),
        )
        self.fq_eps = pd.concat([estimated_eps_series, self.fq_eps])

        ## Chart history 20y (omit latest value, as this is datetime not date)
        hist20 = self.ticker.history(period="20y", interval="1d", adj_timezone=False)[
            "close"
        ][self.symbol]
        self.history_20y = pd.Series(
            hist20.values[:-1], pd.DatetimeIndex(hist20.index[:-1]).tz_localize(None)
        )

        # Chart history 5y
        five_years_ago = self.history_20y.index[-1] - pd.Timedelta(days=365 * 5)
        self.history_5y = self.history_20y.truncate(before=five_years_ago)

    def get_eps_estimates(self, earnings_trend: dict):
        """Extract current and next year EPS estimates and yearAgoEps"""
        current = next((p for p in earnings_trend if p["period"] == "0y"), None)
        next_y = next((p for p in earnings_trend if p["period"] == "+1y"), None)
        return current, next_y
