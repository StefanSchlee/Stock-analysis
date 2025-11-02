# tests/test_stock_analysis.py
import pytest
from stock_analysis import make_stock_analysis

# Example list of stock symbols to test
STOCK_SYMBOLS = ["AAPL", "MSFT", "GOOG", "TSLA"]


@pytest.mark.parametrize("symbol", STOCK_SYMBOLS)
def test_make_stock_analysis(symbol, tmp_path):
    """
    Test the make_stock_analysis function with multiple stock symbols.
    - Figures are not shown
    - PDF is saved to a temporary directory
    """

    # Call the function
    make_stock_analysis(symbol=symbol, show_figures=False, save_to_pdf=True)
