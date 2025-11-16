# Python Stock Analysis

[![Tests](https://github.com/StefanSchlee/Stock-analysis/actions/workflows/python-tests.yml/badge.svg)](https://github.com/StefanSchlee/Stock-analysis/actions/workflows/python-tests.yml)


This project is inspired by existing investor tools (for example, [Aktienfinder](https://aktienfinder.net) and [Eulerpool](https://eulerpool.com)) that visualize price charts and fundamental data using intuitive plots. The goal is to help investors quickly assess whether a stock appears undervalued based on the available data.

I started this project because I was frequently unsatisfied with available tools — no single website provided all the features I wanted, and some useful features were hidden behind paywalls. For example, logarithmic plots of price and fundamental data are rarely available together.

## Usage
The primary entry point is the `make_stock_analysis` function in the `stock_analysis` python package:
- select a stock by its ticker
- decide if interactive matplotlib plots should be opened
- decide if all plots should be exported to a pdf

See the `run_analysis.py` script for usage.

Note that the stock_analysis package is not published to pypi, there you must install the package locally using `pip install -e .`