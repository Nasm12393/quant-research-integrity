# Pine Script integrity fixture P01

This fully synthetic pair demonstrates a bounded source review. The two
strategies use the same simple higher-timeframe crossover idea, cost settings
and order instructions.

- `P01_clean_confirmed_htf.pine` requests the previous confirmed
  higher-timeframe close and restricts decisions to confirmed chart bars.
- `P01_contaminated_future_htf.pine` deliberately exposes the current
  higher-timeframe close too early on historical bars and does not require a
  confirmed chart bar before deciding.

The fixture proves that the two source-level defects can be identified and
reported with exact line references. Both files were compiled and produced a
strategy report in the controlled TradingView run recorded in
`docs/PINE_TRADINGVIEW_EXECUTION_2026-09-20.md`. That observation does not prove
fill realism, alert or webhook delivery, broker execution, live behavior or
profitability; those items remain `NOT VERIFIED`.

See `docs/PINE_AUDIT_SAMPLE_EN.md` for the findings and reproduction protocol.
