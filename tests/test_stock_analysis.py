# tests/test_stock_analysis.py
import pytest
from stock_analysis import make_stock_analysis

# Example list of stock symbols to test
STOCK_SYMBOLS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOG",  # Alphabet
    "TSLA",  # Tesla
    "AMZN",  # Amazon
    "NVDA",  # NVIDIA
    "NFLX",  # Netflix
    "JPM",  # JPMorgan Chase
    "V",  # Visa
    "JNJ",  # Johnson & Johnson
    "UNH",  # UnitedHealth Group
    "XOM",  # ExxonMobil
    "KO",  # Coca-Cola
    "PEP",  # PepsiCo
    "DIS",  # Walt Disney
    "NKE",  # Nike
    "INTC",  # Intel
    "INTU",  # Intuit
]


@pytest.mark.parametrize("symbol", STOCK_SYMBOLS)
def test_make_stock_analysis(symbol, tmp_path):
    """
    Test the make_stock_analysis function with multiple stock symbols.
    - Figures are not shown
    - PDF is saved to a temporary directory
    """

    # Call the function
    make_stock_analysis(symbol=symbol, show_figures=False, save_to_pdf=True)
