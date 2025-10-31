import finqual as fq

ticker = "AAPL"
fq_obj = fq.Finqual(ticker)

income_df = fq_obj.income_stmt_period(2000, 2030)
balance_df = fq_obj.balance_sheet_period(2000, 2030)
cashflow_df = fq_obj.cash_flow_period(2000, 2030)

profitability_df = fq_obj.profitability_ratios_period(2000, 2030)
valuation_df = fq_obj.valuation_ratios_period(2000, 2030)

comparison_companies = fq.CCA(ticker).get_c()
comparison_liquidity = fq.CCA(ticker).liquidity_ratios(2024)
comparison_valuation = fq.CCA(ticker).valuation_ratios()

print(income_df.head())
