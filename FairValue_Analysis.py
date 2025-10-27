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
symbol = "AAPL"
# symbol = 'ADBE'
# symbol = 'NFLX'
# symbol = '7CD.BE'
# symbol = 'MNST'
# symbol = 'MSFT'
# symbol = 'AMZN'
# symbol = 'SBUX'
# symbol = 'PUP'
# symbol = 'AMD'
###########################

print(f"Starting Analysis for {symbol} ...")

plot_manager = PlotManager(2, 2)
stock = StockData(symbol)

# EPS estimates
currentYearEarningEstimateDict, nextYearEarningsEstimateDict = stock.get_eps_estimates()
print(
    f"Last year eps estimate: {currentYearEarningEstimateDict['earningsEstimate']['yearAgoEps']}"
)
print(
    f"Current year eps estimate: {currentYearEarningEstimateDict['earningsEstimate']['avg']}"
)
print(
    f"Next year eps estimate: {nextYearEarningsEstimateDict['earningsEstimate']['avg']}"
)

# --- EPS History ---
dates = stock.income_statement["date"]
lasteps = stock.income_statement["BasicEPS"]

ax = plot_manager.next_axis("Gewinn pro Aktie (raw Data)")
ax.bar(dates.array.date, lasteps, width=pd.Timedelta(days=30), label="Historic EPS")
ax.bar(
    pd.Timestamp(currentYearEarningEstimateDict["endDate"]),
    currentYearEarningEstimateDict["earningsEstimate"]["avg"],
    width=pd.Timedelta(days=30),
    label="Estimate +0y",
)
ax.bar(
    pd.Timestamp(nextYearEarningsEstimateDict["endDate"]),
    nextYearEarningsEstimateDict["earningsEstimate"]["avg"],
    width=pd.Timedelta(days=30),
    label="Estimate +1y",
)
ax.bar(
    dates.array.date[-1],
    currentYearEarningEstimateDict["earningsEstimate"]["yearAgoEps"],
    width=pd.Timedelta(days=10),
    label="Estimate -1y",
)

# --- shares ---
ax = plot_manager.next_axis("Number of shares")
ax.bar(
    stock.number_of_shares.index,
    stock.number_of_shares.array,
    width=pd.Timedelta(days=30),
)

# --- Cashflow ---
CashFlowSeries = stock.cash_flow
ax = plot_manager.next_axis("Cashflow")
ax.bar(
    CashFlowSeries.index,
    CashFlowSeries.array,
    width=pd.Timedelta(days=30),
    label="Historic Operative Cashflow",
)

# --- Corrected EPS ---
EPScorrectionFactor = (
    lasteps.iloc[-1] / currentYearEarningEstimateDict["earningsEstimate"]["yearAgoEps"]
)
print(f"EPS Correction factor: {EPScorrectionFactor}")

eps_array = lasteps.to_numpy()
eps_array = np.append(
    eps_array,
    currentYearEarningEstimateDict["earningsEstimate"]["avg"] * EPScorrectionFactor,
)
eps_array = np.append(
    eps_array,
    nextYearEarningsEstimateDict["earningsEstimate"]["avg"] * EPScorrectionFactor,
)

eps_dates_array = dates.to_numpy()
eps_dates_array = np.append(
    eps_dates_array, np.datetime64(currentYearEarningEstimateDict["endDate"])
)
eps_dates_array = np.append(
    eps_dates_array, np.datetime64(nextYearEarningsEstimateDict["endDate"])
)

eps_series = pd.Series(eps_array, pd.DatetimeIndex(eps_dates_array))

ax = plot_manager.next_axis("EPS corrected")
ax.bar(eps_series.index, eps_series.array, width=pd.Timedelta(days=30))

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
    chartHistory.array[-1] / eps_series.truncate(after=chartHistory.index[-1]).array[-1]
)
KGVe = (
    chartHistory.array[-1] / eps_series.truncate(before=chartHistory.index[-1]).array[0]
)
print(f"KGV: {KGV}")
print(f"KGVe: {KGVe}")

oldestValidKGVDate = eps_series.index[0] - pd.Timedelta(days=365)
liveKGV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKGVDate).index)
for earningsDate in eps_series.index[::-1]:
    earlierDates = liveKGV.truncate(after=earningsDate.date()).index
    liveKGV[earlierDates] = chartHistory[earlierDates] / eps_series[earningsDate]
liveKGVBounded = liveKGV.clip(lower=0)

ax = plot_manager.next_axis("KGVe")
ax.plot(liveKGV)
ax.plot(liveKGVBounded, "--", label="bounded")
for date in eps_series.index:
    ax.axvline(date, ls="--", c="k")

# --- KCVe ---
oldestValidKCVDate = CashFlowSeries.index[0] - pd.Timedelta(days=365)
liveKCV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKCVDate).index)
for date in CashFlowSeries.index[::-1]:
    earlierDates = liveKCV.truncate(after=date.date()).index
    liveKCV[earlierDates] = chartHistory[earlierDates] / CashFlowSeries[date]

ax = plot_manager.next_axis("KCVe")
ax.plot(liveKCV)
for date in CashFlowSeries.index:
    ax.axvline(date, ls="--", c="k")

# --- Fair Value ---
movingAverageTime = pd.Timedelta(days=365 * 3)
fairValue_value = []
for earningsDate in eps_series.index:
    averagingStartDate = earningsDate - movingAverageTime
    meanKGV = liveKGVBounded.truncate(
        before=averagingStartDate, after=earningsDate
    ).array.mean()
    fairValue_value.append(meanKGV * eps_series[earningsDate])
fairValue = pd.Series(fairValue_value, eps_series.index)

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
