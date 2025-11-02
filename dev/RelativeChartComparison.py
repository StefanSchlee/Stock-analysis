# Task: Compare two stocks

from yahooquery import Ticker
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

###########################
# symbol1 = 'MC.PA'
symbol1 = "SBUX"
symbol2 = "PSA"
###########################

ticker1 = Ticker(symbol1)
ticker2 = Ticker(symbol2)

# get chart
chartHistory1 = ticker1.history(period="5y", interval="1d", adj_timezone=False)[
    "close"
][symbol1]
chartHistory1.index = pd.DatetimeIndex(chartHistory1.index).tz_localize(None)
chartHistory2 = ticker2.history(period="5y", interval="1d", adj_timezone=False)[
    "close"
][symbol2]
chartHistory2.index = pd.DatetimeIndex(chartHistory2.index).tz_localize(None)


# calculate relative chart
relChartHistory1 = pd.Series(
    chartHistory1.array / chartHistory1.array[0] * 100, chartHistory1.index
)
relChartHistory2 = pd.Series(
    chartHistory2.array / chartHistory2.array[0] * 100, chartHistory2.index
)

# plot rel chart history
fig, ax = plt.subplots()
ax.plot(relChartHistory1, label=symbol1)
ax.plot(relChartHistory2, label=symbol2)

ax.grid()
ax.set_title("Relative Chart")
ax.legend()


plt.show()
