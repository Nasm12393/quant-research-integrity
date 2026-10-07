# Controlled TradingView execution - P01

Date: `2026-09-20`
Account: authenticated private TradingView workspace
Purpose: controlled runtime check of two synthetic Pine Script fixtures
Trading boundary: no broker connection, no alert, no webhook and no real order

## Frozen environment

- symbol: `BINANCE:BTCUSDT`;
- chart type: standard candles;
- chart timeframe: `15m`;
- higher-timeframe input: `60m`;
- visible report window: `2026-07-01` to `2026-09-20`;
- Pine Script version: `v6`;
- source-declared commission: `0.10%`;
- source-declared slippage: `2` ticks;
- `process_orders_on_close=true`.

TradingView Basic allowed two indicators on the chart. An unrelated,
pre-existing indicator remained visible while the two P01 fixtures were
inserted one at a time. The active strategy report was checked by name before
each observation. That indicator is not referenced by either P01 source file.

## Source identity

| Fixture | SHA-256 |
| --- | --- |
| `P01_clean_confirmed_htf.pine` | `a3ddf9be658ed65ecec83800a07b2f668eb3f95b3a11360756dd8e904851ebe1` |
| `P01_contaminated_future_htf.pine` | `61ac824ef36c69bd82dffb4384c7787186074cf1e31905a1c20f7dbaec8cb355` |

## Observed execution

| Observation | Clean fixture | Contaminated fixture |
| --- | --- | --- |
| Saved as a separate private script | Yes | Yes |
| Compiled and added to chart | Yes | Yes |
| Active strategy report opened | Yes | Yes |
| Closed trades displayed | `1,120` | `989` |
| Winning trades displayed | `159` (`14.20%`) | `21` (`2.12%`) |
| Profit factor displayed | `0.245` | `0.009` |
| Total P&L displayed | `-150,950.89 USDT` (`-15.10%`) | `-314,649.47 USDT` (`-31.46%`) |
| TradingView look-ahead warning visible in the active fixture report | No | No |

The figures are recorded only to prove that TradingView executed the two
sources and produced materially different event paths. They are not evidence
of profitability, realistic sizing or executable fills. Default strategy
capital and quantity settings were not normalized for an economic comparison.

## Controlled conclusion

1. Both frozen fixtures compile and execute in TradingView on the stated
   standard chart.
2. The deliberate source changes alter the generated trade path materially.
3. TradingView displayed no look-ahead warning while the deliberately
   contaminated fixture was the active strategy report.
4. Therefore a successful compilation, an active report and the absence of a
   platform warning do not replace source-level chronology review.
5. Broker-emulator fill realism, alerts, webhooks, live behavior and future
   profitability remain `NOT VERIFIED`.

The clean fixture was restored as the active strategy report after the test.
No trade was placed.
