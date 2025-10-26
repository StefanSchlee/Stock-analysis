#tested with python 3.11

from yahooquery import Ticker
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg'
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline, pchip_interpolate
from PlotManager import PlotManager


###########################
# symbol = 'MC.PA'
# symbol = 'PAYC'
# symbol = 'PYPL'
symbol = 'AAPL'
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

# Plotmanager instance
plot_manager = PlotManager(2,2)

ticker = Ticker(symbol)

earningsTrend = ticker.earnings_trend
earningsTrend = earningsTrend[symbol]['trend']

# print(len(earningsTrend))
# print(earningsTrend)

#extract estimate of current year
currentYearEarningEstimateDict = None
nextYearEarningsEstimateDict = None
for period in earningsTrend:
    if period['period'] == "0y":
        currentYearEarningEstimateDict = period
    if period['period'] == "+1y":
        nextYearEarningsEstimateDict = period

print(f"Last year eps estimate: {currentYearEarningEstimateDict['earningsEstimate']['yearAgoEps']}")
print(f"Current year eps estimate: {currentYearEarningEstimateDict['earningsEstimate']['avg']}")
print(f"Next year eps estimate: {nextYearEarningsEstimateDict['earningsEstimate']['avg']}")


#extract eps of last four years
lastIncome = ticker.income_statement(trailing=False)
dates = lastIncome['asOfDate']
years = dates.dt.year
lasteps = lastIncome['BasicEPS']

ax = plot_manager.next_axis("Gewinn pro Aktie (raw Data)")
ax.bar(dates.array.date, lasteps, width=pd.Timedelta(days=30), label="Historic EPS")
ax.bar(pd.Timestamp(currentYearEarningEstimateDict['endDate']), currentYearEarningEstimateDict['earningsEstimate']['avg'], width=pd.Timedelta(days=30), label="Estimate +0y")
ax.bar(pd.Timestamp(nextYearEarningsEstimateDict['endDate']), nextYearEarningsEstimateDict['earningsEstimate']['avg'], width=pd.Timedelta(days=30), label='Estimate +1y')
ax.bar(dates.array.date[-1], currentYearEarningEstimateDict['earningsEstimate']['yearAgoEps'], width=pd.Timedelta(days=10), label="Estimate -1y")


#extract cashflow of last years, create Cashflow series
LastCashFlow = ticker.cash_flow()
CashFlowDates = LastCashFlow['asOfDate']
OperativeCashFlow = LastCashFlow['CashFlowFromContinuingOperatingActivities']
CashFlowSeries = pd.Series(OperativeCashFlow.array, CashFlowDates)

ax = plot_manager.next_axis("Cashflow")
ax.bar(CashFlowSeries.index, OperativeCashFlow.array, width=pd.Timedelta(days=30), label="Historic Operative Cashflow")


#eps estimate correction (divergence between eps calculation of estimate and history, see GAAP, non-GAAP)
EPScorrectionFactor = lasteps[-1] / currentYearEarningEstimateDict['earningsEstimate']['yearAgoEps']
print(f"EPS Correction factor: {EPScorrectionFactor}")

#create eps series
eps_array = lasteps.to_numpy()
eps_array = np.append(eps_array, currentYearEarningEstimateDict['earningsEstimate']['avg'] * EPScorrectionFactor)
eps_array = np.append(eps_array, nextYearEarningsEstimateDict['earningsEstimate']['avg'] * EPScorrectionFactor)

eps_dates_array = dates.to_numpy()
eps_dates_array= np.append(eps_dates_array,np.datetime64(currentYearEarningEstimateDict['endDate']))
eps_dates_array= np.append(eps_dates_array,np.datetime64(nextYearEarningsEstimateDict['endDate']))

eps_series = pd.Series(eps_array,pd.DatetimeIndex(eps_dates_array))

ax = plot_manager.next_axis("EPS corrected")
ax.bar(eps_series.index, eps_series.array , width=pd.Timedelta(days=30))

#get chart history
chartHistory = ticker.history(period='5y',interval='1d',adj_timezone=False)['close'][symbol]
chartHistory.index = pd.DatetimeIndex(chartHistory.index).tz_localize(None)

ax = plot_manager.next_axis("Chart 5y")
ax.plot(chartHistory)

# current KGV
KGV = chartHistory.array[-1] / eps_series.truncate(after=chartHistory.index[-1]).array[-1]
KGVe = chartHistory.array[-1] / eps_series.truncate(before=chartHistory.index[-1]).array[0]
print(f"KGV: {KGV}")
print(f"KGVe: {KGVe}")

#live KGV
oldestValidKGVDate = eps_series.index[0] - pd.Timedelta(days=365)
liveKGV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKGVDate).index)
for earningsDate in eps_series.index[::-1]:
    earlierDates = liveKGV.truncate(after=earningsDate.date()).index
    liveKGV[earlierDates] = chartHistory[earlierDates] / eps_series[earningsDate]

#for calculation of fair value, lower bound KGV to zero in case the EPS were negative
liveKGVBounded = liveKGV.clip(lower=0)

ax = plot_manager.next_axis("KGVe")
ax.plot(liveKGV)
ax.plot(liveKGVBounded, '--', label="bounded")
for date in eps_series.index:
    ax.axvline(date,ls='--',c='k')

# live KCV
oldestValidKCVDate = CashFlowSeries.index[0] - pd.Timedelta(days=365)
liveKCV = pd.Series(np.nan, chartHistory.truncate(before=oldestValidKCVDate).index)
for date in CashFlowSeries.index[::-1]:
    earlierDates = liveKCV.truncate(after=earningsDate.date()).index
    liveKCV[earlierDates] = chartHistory[earlierDates] / CashFlowSeries[date]

ax = plot_manager.next_axis("KCVe")
ax.plot(liveKCV)
for date in CashFlowSeries.index:
    ax.axvline(date,ls='--',c='k')

#fair value at earnings release (doku in eulerpool pinned post)
movingAverageTime = pd.Timedelta(days=365*3)
fairValue_value = []

for earningsDate in eps_series.index:
    averagingStartDate = (earningsDate-movingAverageTime)

    #average over all data availabe, but maximal over <movingAverageTime>
    meanKGV = liveKGVBounded.truncate(before=averagingStartDate,after=earningsDate).array.mean()
    fairValue_value.append(meanKGV*eps_series[earningsDate])
fairValue = pd.Series(fairValue_value, eps_series.index)

#interpolate fair value
# fairValueSpline = CubicSpline(fairValue.index.values.astype('float'),fairValue.array, bc_type='natural')
# fairValueDateFine = np.linspace(fairValue.index.values[0].astype('float'),fairValue.index.values[-1].astype('float'),1000)
# fairValueFine = fairValueSpline(fairValueDateFine)

fairValueDateFine = np.linspace(fairValue.index.values[0].astype('float'),fairValue.index.values[-1].astype('float'),1000)
fairValueFine = pchip_interpolate(fairValue.index.values.astype('float'),fairValue.array, fairValueDateFine)



ax = plot_manager.next_axis("Fair value (KGV)")
ax.plot(chartHistory, label="Kurs")

# ax.plot(fairValue)
ax.plot(fairValue.index, fairValue.array, ls='', marker='x', label="Fair value",c='k')
ax.plot(pd.to_datetime(fairValueDateFine), fairValueFine, label=None, c='k')
# +-20% fair Value
ax.plot(pd.to_datetime(fairValueDateFine), 1.2*fairValueFine, label="+20%", c='r')
ax.plot(pd.to_datetime(fairValueDateFine), 0.8*fairValueFine, label="-20%", c='g')


plot_manager.finalize()
pass
