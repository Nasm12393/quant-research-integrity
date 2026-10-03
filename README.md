# Quant Research Integrity Auditor

An offline, dependency-free demonstrator for auditing the plumbing beneath a
quantitative backtest.

It does not search for alpha, optimize parameters, connect to an exchange, or
place orders. It checks whether a research dataset respects the facts that a
backtest usually assumes.

## Checks

- feature timestamps never extend beyond decision timestamps;
- executions never precede decisions;
- every market and signal row belongs to an explicit contract life;
- relisted symbols remain separated by `life_id`;
- rows before listing or after cessation are rejected;
- flat zero-volume post-cessation archive stubs are identified;
- duplicate observations are rejected;
- optional SHA-256 manifests are verified without path traversal.

## Demonstration

Run the clean fixture first:

```powershell
python -m quant_integrity `
  --lives examples\clean\lives.csv `
  --market examples\clean\market.csv `
  --signals examples\clean\signals.csv `
  --manifest examples\clean\SHA256SUMS.txt
```

It exits with code `0` and reports `PASS`.

The supplied synthetic dataset intentionally contains one look-ahead signal
and one post-cessation archive stub:

```powershell
python -m quant_integrity `
  --lives examples\lives.csv `
  --market examples\market.csv `
  --signals examples\signals.csv `
  --manifest examples\SHA256SUMS.txt
```

The command exits with code `2` and reports `FAIL`. Invalid schemas or
unreadable files exit with code `3`.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Commercial boundary

This tool can support a reproducibility or market-data quality audit. It never
certifies profitability, future performance, or suitability for live trading.

## Bounded review service

Need an independent check of one reported backtest result?

- **Integrity screening - EUR 100:** one documented tabular export, five
  priority checks, and a concise `PASS / FAIL / NOT VERIFIED` matrix.
- **Reproducible pilot - EUR 390:** one code package, one strategy, one
  documented dataset, and one result, with an evidence-backed report.

No broker access, trading account, API key, or performance promise is involved.
The EUR 100 screening is credited toward the EUR 390 pilot when both cover the
same case. Scope and payment must be agreed before any client artifact is sent.

Contact: `b.m.nassim85@gmail.com`

The fully synthetic engineering case study is available in
`docs/CASE_STUDY.md`. It contains no production dataset, strategy, account,
credential, or private research identifier. Publication remains subject to the
checks in `docs/PUBLICATION_CHECKLIST.md` and a separate human review.

A concise French guide to the most common integrity failures is available in
`docs/CINQ_ERREURS_BACKTEST.md`.

## Sample reports

Two fully synthetic, three-page sample reports show the evidence standard and
the boundary of a real screening deliverable:

- [English sample report](public_demo/sample_backtest_integrity_report_en.pdf);
- [rapport exemple en francais](public_demo/rapport_exemple_integrite_backtest_fr.pdf).

Their detailed, inspectable source versions are available in
[English](docs/SAMPLE_INTEGRITY_REPORT_EN.md) and
[French](docs/SAMPLE_INTEGRITY_REPORT_FR.md). They contain no client artifact
or private research observation.

## Pine Script source-review fixture

A bounded synthetic Pine example is available in `examples/pine/`. It pairs a
future-leaking higher-timeframe request with a corrected confirmed-value
version. The line-by-line matrix in `docs/PINE_AUDIT_SAMPLE_EN.md` demonstrates
the source review and states which runtime claims remain `NOT VERIFIED`.

This fixture is not a Pine parser and does not certify TradingView fills,
webhooks, broker execution or future profitability.

Both fixtures were also compiled and executed in one frozen TradingView setup.
The controlled runtime record is in
`docs/PINE_TRADINGVIEW_EXECUTION_2026-09-20.md`. TradingView produced materially
different trade paths but displayed no look-ahead warning for the deliberately
contaminated fixture. This establishes why successful compilation and a visible
strategy report do not replace source-level chronology review. It does not
establish realistic fills, live behavior or future profitability.

## TradingView automation incident sample

A separate synthetic report demonstrates a bounded reconstruction of one
disputed alert-to-order incident. It preserves the enrolled configuration,
distinguishes one originating alert from repeated webhook delivery attempts,
and traces connector submissions to broker records without inferring missing
evidence.

- [Six-page incident audit sample](public_demo/TRADINGVIEW_INCIDENT_AUDIT_SAMPLE_REPORT_2026-10-01.pdf)
- [Inspectable report source](docs/TRADINGVIEW_INCIDENT_AUDIT_SAMPLE_REPORT_2026-10-01.md)

The scenario is entirely invented. It is not a customer audit, platform
certification, execution guarantee, trading recommendation or performance
assessment.

## Service boundary

Commercial drafts are maintained outside the future public release. Their
presence in this private working repository is not evidence of customer demand
and does not authorize outreach. The public release is exported from the
explicit allowlist in `docs/PUBLIC_RELEASE_MANIFEST.txt`.

## License

Copyright (c) 2026 Nassim Berrahmane. Released under the MIT License; see
`LICENSE`.
