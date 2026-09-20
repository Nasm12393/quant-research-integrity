# Sample Pine Script integrity review P01

**Scope:** two fully synthetic Pine Script v6 source files
**Purpose:** demonstrate a bounded source review, not strategy validation
**Verdict:** contaminated fixture `FAIL`; clean fixture `PASS` for the two
source-level controls tested here

## Evidence matrix

| Check | Clean fixture | Contaminated fixture | Evidence |
| --- | --- | --- | --- |
| Confirmed higher-timeframe value | `PASS` | `FAIL` | Clean lines 13-17 offset the expression with `close[1]`; contaminated lines 13-17 use the current HTF `close` with `lookahead_on`. |
| Confirmed chart-bar decision | `PASS` | `FAIL` | Clean lines 19-20 require `barstate.isconfirmed`; contaminated lines 20-21 do not. |
| Costs declared in source | `PASS` | `PASS` | Lines 5-7 in both fixtures declare commission and slippage assumptions. Their realism is not certified. |
| Standard versus synthetic chart | `PASS` for the controlled run | `PASS` for the controlled run | Both files were executed on standard `BINANCE:BTCUSDT` candles at `15m`; this does not generalize to another chart setting. |
| TradingView compilation and report generation | `PASS` | `PASS` | Both private copies compiled and produced an active strategy report on 2026-09-20. |
| Broker-emulator fill behavior | `NOT VERIFIED` | `NOT VERIFIED` | Runtime reports exist, but quantity defaults and fill realism were not independently validated. |
| Alert versus strategy consistency | `NOT VERIFIED` | `NOT VERIFIED` | These bounded fixtures define no alert or webhook path. |
| Live execution or future profitability | Out of scope | Out of scope | A source review cannot establish either claim. |

## Findings

### P01-F01 - future higher-timeframe value on historical bars

**Status:** `FAIL` in the contaminated fixture.

`P01_contaminated_future_htf.pine:16` requests the current higher-timeframe
`close` while using `barmerge.lookahead_on`. On historical chart bars, this can
make the final value of the higher-timeframe bar appear before it was available
to a live decision.

The clean fixture uses `close[1]` at line 16. This deliberately requests the
previous completed higher-timeframe value. The conclusion is limited to this
explicit pattern and is not a claim that every `request.security()` construction
can be classified by a text scan.

### P01-F02 - decision not restricted to a confirmed chart bar

**Status:** `FAIL` in the contaminated fixture.

The conditions at lines 20-21 can change while the chart bar is still open.
Whether that creates a user-visible discrepancy depends on strategy settings,
alerts and runtime behavior, so the downstream impact remains `NOT VERIFIED`.

The clean fixture makes the intended timing explicit with
`barstate.isconfirmed` at lines 19-20.

## Minimal corrective action

1. Offset the higher-timeframe expression to the previous completed value when
   using this confirmed-HTF pattern.
2. Require a confirmed chart bar when the intended decision rule is
   close-of-bar only.
3. Re-run the corrected source under frozen TradingView settings and retain the
   properties screenshot and exported trade list.

## Reproduction protocol

A controlled TradingView execution was completed on `2026-09-20`. The factual
record is retained in `docs/PINE_TRADINGVIEW_EXECUTION_2026-09-20.md`. The run
froze the following:

- TradingView Pine Script v6;
- one named exchange symbol;
- standard candles, not Heikin Ashi, Renko or another synthetic chart;
- chart timeframe `15m` and higher timeframe input `60m`;
- one fixed date window;
- unchanged strategy properties, including commission and slippage;
- SHA-256 hashes from `examples/pine/SHA256SUMS.txt`.

Both files compiled. The clean report displayed `1,120` closed trades and the
contaminated report displayed `989`. TradingView showed no look-ahead warning
while the deliberately contaminated fixture was the active report. This is a
runtime observation, not a profitability comparison: sizing defaults, fill
realism, alerts and live behavior remain `NOT VERIFIED`. This sample does not use a Pine parser and does not claim automated coverage of arbitrary Pine
Script programs.
