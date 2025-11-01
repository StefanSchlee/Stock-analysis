# tested with python 3.11

from yahooquery import Ticker
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")  # or 'Qt5Agg'
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline, pchip_interpolate
from PlotManager import PlotManager
from scipy.stats import linregress
from StockData import StockData


###########################
# symbol = 'MC.PA'
# symbol = 'PAYC'
# symbol = 'PYPL'
# symbol = "AAPL"
# symbol = 'ADBE'
# symbol = 'NFLX'
# symbol = '7CD.BE'
# symbol = "MNST"
symbol = "MSFT"
# symbol = "AMZN"
# symbol = 'SBUX'
# symbol = 'PUP'
# symbol = 'AMD'
###########################

print(f"Starting Analysis for {symbol} ...")

plot_manager = PlotManager(2, 2)
stock = StockData(symbol)


# --- shares ---
ax = plot_manager.next_axis("Number of shares")
ax.bar(
    stock.fq_balance_df.index,
    stock.fq_balance_df["Shares Outstanding"].array,
    width=pd.Timedelta(days=30),
    label="finqual",
)

# --- Cashflow ---
ax = plot_manager.next_axis("Cashflow")
ax.bar(
    stock.fq_cashflow_df.index,
    stock.fq_cashflow_df["Operating Cash Flow"].array,
    width=pd.Timedelta(days=30),
)

# --- Corrected EPS
ax = plot_manager.next_axis("EPS Correction")
ax.bar(
    stock.fq_eps.index,
    stock.fq_eps.array,
    width=pd.Timedelta(days=30),
    label="finqual+corrected estimates",
)
ax.bar(
    stock.income_statement["asOfDate"],
    stock.income_statement["BasicEPS"],
    width=pd.Timedelta(days=20),
    label="yahoo eps",
)
ax.bar(
    pd.Timestamp(stock.yh_current_year_estimates["endDate"]),
    stock.yh_current_year_estimates["earningsEstimate"]["avg"],
    width=pd.Timedelta(days=20),
    label="Estimate +0y",
)
ax.bar(
    pd.Timestamp(stock.yh_next_year_estimates["endDate"]),
    stock.yh_next_year_estimates["earningsEstimate"]["avg"],
    width=pd.Timedelta(days=20),
    label="Estimate +1y",
)
ax.bar(
    stock.income_statement["asOfDate"].iloc[-1],
    stock.yh_current_year_estimates["earningsEstimate"]["yearAgoEps"],
    width=pd.Timedelta(days=10),
    label="Estimate -1y",
)

# --- 20-Year Chart with Phases ---
chartHistory = stock.history_20y.dropna()
n = len(chartHistory)
split_points = [n // 3, 2 * n // 3]
phases = [
    chartHistory.iloc[: split_points[0]],
    chartHistory.iloc[split_points[0] : split_points[1]],
    chartHistory.iloc[split_points[1] :],
]


def mean_annual_growth(series: pd.Series):
    start_price = series.iloc[0]
    end_price = series.iloc[-1]
    years = (series.index[-1] - series.index[0]).days / 365.25
    if start_price <= 0 or years == 0:
        return np.nan
    return (end_price / start_price) ** (1 / years) - 1


fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(chartHistory, color="black", linewidth=1, label=f"{symbol} Closing Price (20y)")
ax.set_yscale("log")
ax.set_title(f"{symbol} – 20-Year Logarithmic Price Chart with Growth Phases")
ax.set_xlabel("Date")
ax.set_ylabel("Price (log scale)")
ax.grid(True, which="both", ls="--", alpha=0.6)

colors = ["#f4cccc", "#d9ead3", "#cfe2f3"]
for i, phase in enumerate(phases):
    ax.axvspan(phase.index[0], phase.index[-1], color=colors[i], alpha=0.25)

    # CAGR
    growth = mean_annual_growth(phase)

    # Regression line
    x = np.arange(len(phase)) / 252
    y = np.log(phase.values)
    slope, intercept, r, p, se = linregress(x, y)
    y_fit = np.exp(intercept + slope * x)
    ax.plot(phase.index, y_fit, color="red", linestyle="--", linewidth=1.2)

    mid_date = phase.index[len(phase) // 2]
    ax.text(
        mid_date,
        chartHistory.max(),
        f"{growth*100:.2f}%/yr",
        ha="center",
        va="top",
        fontsize=9,
        fontweight="bold",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

# --- KGV ---
KGV = (
    chartHistory.array[-1]
    / stock.fq_eps.truncate(before=chartHistory.index[-1]).array[0]
)
KGVe = (
    chartHistory.array[-1]
    / stock.fq_eps.truncate(after=chartHistory.index[-1]).array[-1]
)

oldestValidKGVDate = stock.fq_eps.index[-1] - pd.Timedelta(days=365)
liveKGV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKGVDate).index)
for earningsDate in stock.fq_eps.index:
    earlierDates = liveKGV.truncate(after=earningsDate.date()).index
    liveKGV[earlierDates] = chartHistory[earlierDates] / stock.fq_eps[earningsDate]
liveKGVBounded = liveKGV.clip(lower=0)

ax = plot_manager.next_axis(f"KGV: {KGV:.1f}, KGVe: {KGVe:.1f}")
ax.plot(liveKGV, label="live KGVe")
ax.plot(liveKGVBounded, "--", label="bounded")
for date in stock.fq_eps.index:
    ax.axvline(date, ls="--", c="k")

# --- KCVe ---
# oldestValidKCVDate = stock.cash_flow_per_share.index[0] - pd.Timedelta(days=365)
# liveKCV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKCVDate).index)
# for date in stock.cash_flow_per_share.index[::-1]:
#     earlierDates = liveKCV.truncate(after=date.date()).index
#     liveKCV[earlierDates] = chartHistory[earlierDates] / stock.cash_flow_per_share[date]

# ax = plot_manager.next_axis(f"KCVe: {liveKCV.values[-1]:.1f}")
# ax.plot(liveKCV)
# for date in stock.cash_flow_per_share.index:
#     ax.axvline(date, ls="--", c="k")

# --- Fair Value ---
movingAverageTime = pd.Timedelta(days=365 * 3)
fairValue_value = []
for earningsDate in stock.fq_eps.index:
    averagingStartDate = earningsDate - movingAverageTime
    meanKGV = liveKGVBounded.truncate(
        before=averagingStartDate, after=earningsDate
    ).array.mean()
    fairValue_value.append(meanKGV * stock.fq_eps[earningsDate])
fairValue = pd.Series(fairValue_value, stock.fq_eps.index)
fairValue = fairValue.iloc[::-1].copy()  # make it ascending order

fairValueDateFine = np.linspace(
    fairValue.index.values[0].astype("float"),
    fairValue.index.values[-1].astype("float"),
    1000,
)
fairValueFine = pchip_interpolate(
    fairValue.index.values.astype("float"), fairValue.array, fairValueDateFine
)

ax = plot_manager.next_axis("Fair value (KGV)")
ax.plot(chartHistory, label="Kurs")
ax.plot(fairValue.index, fairValue.array, ls="", marker="x", label="Fair value", c="k")
ax.plot(pd.to_datetime(fairValueDateFine), fairValueFine, c="k")
ax.plot(pd.to_datetime(fairValueDateFine), 1.2 * fairValueFine, label="+20%", c="r")
ax.plot(pd.to_datetime(fairValueDateFine), 0.8 * fairValueFine, label="-20%", c="g")
ax.set_xlim(fairValue.index[0], fairValue.index[-1])

plot_manager.finalize()
