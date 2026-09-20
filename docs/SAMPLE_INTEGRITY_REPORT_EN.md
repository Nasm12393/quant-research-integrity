# Sample report - backtest integrity screening

**Nature:** fully synthetic and reproducible demonstration  
**Author:** Nassim Berrahmane  
**Date:** 2026-09-06  
**Audited version:** `public-sample-v1`
**Overall verdict for the contaminated fixture:** `FAIL`

> This document demonstrates the form and evidence standard of a bounded
> screening. It contains no client data, private strategy, position, API key,
> or observation from the private research laboratory.

## 1. Audit question

Does the supplied dataset satisfy the minimum chronology, instrument-life and
file-integrity properties required to defend a reported backtest result?

The screening compares two inspectable fixtures:

- a clean reference used as a positive control;
- a contaminated variant containing exactly two deliberate defects.

The audit does not search for alpha or recompute performance.

## 2. Scope

| Item | Included | Result |
| --- | --- | --- |
| SHA-256 manifests | Yes | 3 files verified per fixture |
| Tabular schema | Yes | Readable and conforming |
| Feature -> decision chronology | Yes | One look-ahead detected |
| Instrument life `(symbol, life_id)` | Yes | One post-cessation row detected |
| Duplicate observations | Yes | None in this fixture |
| Fees, spread, slippage and liquidity | No | `NOT VERIFIED` |
| Return, causality and live suitability | No | Out of scope |

## 3. Reproducible method

The same offline auditor was executed twice, without network access or a
trading account dependency.

```powershell
python -m quant_integrity `
  --lives examples\clean\lives.csv `
  --market examples\clean\market.csv `
  --signals examples\clean\signals.csv `
  --manifest examples\clean\SHA256SUMS.txt
```

Expected and observed result: `PASS`, exit code `0`, zero findings.

```powershell
python -m quant_integrity `
  --lives examples\lives.csv `
  --market examples\market.csv `
  --signals examples\signals.csv `
  --manifest examples\SHA256SUMS.txt
```

Expected and observed result: `FAIL`, exit code `2`, two findings.

## 4. Verdict matrix

| Control | Verdict | Factual evidence |
| --- | --- | --- |
| File integrity | `PASS` | 3 manifest entries verified |
| Contract-life catalogue | `PASS` | 3 contract lives checked |
| Signal chronology | `FAIL` | `LOOKAHEAD`, `signals.csv`, row 2 |
| Rows after cessation | `FAIL` | `PHANTOM_POST_CESSATION_ROW`, `market.csv`, row 3 |
| Relisting separation | `PASS` | Composite `(symbol, life_id)` key enforced |
| Real execution cost | `NOT VERIFIED` | No client book, order or fee schedule supplied |

## 5. Priority findings

### F-01 - Feature available after the decision

**Severity:** high  
**Code:** `LOOKAHEAD`  
**Evidence:** the feature window in `signals.csv`, row 2, ends after the
decision timestamp.

**Plausible impact:** the signal uses information that would not have been
available at the simulated decision time. The associated performance cannot
be defended as point-in-time. No numerical impact is claimed because this
screening does not recompute returns.

**Minimum remediation:** rebuild the feature with an end timestamp no later
than the decision and regenerate the result from frozen inputs.

### F-02 - Phantom observation after cessation

**Severity:** high  
**Code:** `PHANTOM_POST_CESSATION_ROW`  
**Evidence:** `market.csv`, row 3, contains a flat zero-volume observation
after cessation of `('ABCUSDT', 'life-1')`.

**Plausible impact:** an archive can make a non-tradable observation appear
tradable and can mix an old contract life with a later relisting. No PnL effect
is quantified in this screening.

**Minimum remediation:** mechanically reject every row outside
`[life_start, cessation_at]` and retain `life_id` in every join.

## 6. Traceability

| File | SHA-256 |
| --- | --- |
| `examples/clean/lives.csv` | `981543F97A8DBCAB7DA29D4C29E667F25C26E153A9715A01ED7ED879E145FA5F` |
| `examples/clean/market.csv` | `F1D5DD52F6B012AC0E8522DFE292EFBD8CFE1E9E853E0090D81DE91391D6F51C` |
| `examples/clean/signals.csv` | `FDBCCD944A6573E6290E7FD859223E6274D985C2BA144C966C0B8DED0929D0B8` |
| `examples/market.csv` | `1DF2920DBCC1B7B8EFFB01C68841E9C49A7AEE61B40E0F037C9FCF0B54BB6DF5` |
| `examples/signals.csv` | `DF08E8A0DB144EF2FB91F6075E8B2F984D341762D01E5D33DEAEA43113465D2B` |

## 7. Conclusion

The contaminated fixture fails for two reproducible and localized reasons.
The clean fixture passes the same controls, demonstrating that the auditor
does not reject every input indiscriminately.

This verdict establishes dataset and chronology properties only. It does not
certify real-source completeness, economic causality, future performance, or
suitability for live trading.
