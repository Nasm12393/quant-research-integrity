# Case Study: Detecting Temporal and Contract-Life Leakage

This case study is fully synthetic. Its symbols, dates, prices, counts, and
failure modes are demonstration fixtures rather than production observations.
It discloses no strategy, position, return series, account, credential,
proprietary payload, or private research identifier.

## Problem

Historical perpetual-contract archives may retain rows after an exchange has
officially settled a contract. A symbol may also be relisted later under a new
contract life. A backtest keyed only by symbol can therefore mix independent
lives or treat terminal archive stubs as tradable observations.

## Synthetic scenario

The fixture defines two non-overlapping lives for one fictional symbol and one
life for a second fictional symbol. Its contaminated variant contains exactly
two deliberate defects:

- a flat, zero-volume market row after the first life has ceased;
- a signal whose feature window ends after its decision timestamp.

The clean variant removes both defects. Every input is a small CSV committed
with the demonstrator, so the expected behavior can be inspected without
network access or external data.

## Engineering response

The auditor keys every observation by `(symbol, life_id)`, validates explicit
life boundaries, checks signal chronology, distinguishes empty terminal stubs
from non-empty post-cessation activity, and verifies optional SHA-256
manifests. The clean fixture returns `PASS`; the contaminated fixture returns
`FAIL` with `LOOKAHEAD` and `PHANTOM_POST_CESSATION_ROW` findings.

## Boundary

Passing these checks proves dataset and chronology properties only. It does
not prove data completeness, economic causality, predictive power,
profitability, or suitability for live trading.
