# Python Stock Analysis

(insert tests badge)

This project is inspired by tools like (insert aktienfinder website link, eulerpool link), which visualize stock chart and fundamentals data in intuitive charts. The goal is to support investors to quickly assess if a stock may be currently undervalued based on the data. 

My motivation on this project rise because i was often unsatisfied by the tools mentioned above. There was no single tool or website, which offered all features i wanted, or they are hidden behind a paywall. For example, a logarithmic plot of the chart and fundamental data is found almost nowhere.

## Usage
All functionality is given by the `make_stock_analysis` function in the `stock_analysis` python package:
- select a stock by its ticker
- decide if interactive matplotlib plots should be opened
- decide if all plots should be exported to a pdf

See the `run_analysis.py` script for usage.

Note that the stock_analysis package is not published to pypi, there you must install the package locally using `pip install -e .`