# tested with python 3.11

import stock_analysis

###########################
# symbol = 'MC.PA'
# symbol = 'PAYC'
# symbol = 'PYPL'
symbol = "AAPL"
# symbol = 'ADBE'
# symbol = 'NFLX'
# symbol = '7CD.BE'
# symbol = "MNST"
# symbol = "MSFT"
# symbol = "AMZN"
# symbol = 'SBUX'
# symbol = 'PUP'
# symbol = 'AMD'
###########################

stock_analysis.make_stock_analysis(symbol=symbol, show_figures=False, save_to_pdf=True)
