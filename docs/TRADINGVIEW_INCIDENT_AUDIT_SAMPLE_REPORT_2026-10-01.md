# TradingView automation incident audit - synthetic sample report

Report template version: 2026-10-01

Document status: `SYNTHETIC_SAMPLE_NOT_A_CUSTOMER_AUDIT`

All names, timestamps, identifiers and records in this report are invented.
This sample demonstrates the deliverable format only. It does not describe a
real TradingView, connector or broker incident.

## Report identity

| Field | Value |
| --- | --- |
| Case ID | `SYN-TV-20260930-001` |
| Customer incident label | Synthetic duplicate-order dispute |
| Reviewer | Integrity Research Agent |
| Accepted scope | One BTCUSDT 15-minute long-alert incident |
| Incident window in UTC | 2026-09-30 14:29:55 through 14:30:10 |
| Evidence accepted in UTC | Synthetic pack frozen 2026-10-01 |
| Report issued in UTC | 2026-10-01 |
| Report SHA-256 | Recorded in the adjacent `.sha256` manifest |

This report reconciles records supplied for one bounded incident. It is not a
platform certification, source-code audit, execution guarantee, trading
recommendation or performance assessment.

## Executive verdict

Overall incident status:

`FAIL`

One-sentence finding:

> One recorded TradingView alert was delivered twice after an initial HTTP
> 500 response, and the connector submitted one broker order for each delivery
> attempt instead of collapsing both attempts into one action.

Material limitation:

> The later chart uses script revision `rev-b`, while the enrolled alert used
> `rev-a`; the later chart therefore cannot prove or disprove the original
> realtime signal.

## Question and expected path

Customer question:

> TradingView showed one long alert, but the broker received two long orders.
> The chart now shows no corresponding entry. Did TradingView generate two
> signals, did the connector duplicate one delivery or did the script repaint?

Expected recorded path:

1. TradingView records one originating alert event.
2. The receiver records every webhook delivery attempt.
3. The connector validates the payload and routes the intended action once.
4. The broker records the outcome of the single intended submission.

Observed customer outcome:

> Two broker orders were accepted and filled after one recorded originating
> alert.

## Scope and exclusions

Included:

- alert `A-77` and payload identity `evt-991`;
- records between 2026-09-30 14:29:55 and 14:30:10 UTC;
- the supplied TradingView, configuration, receiver, connector and broker
  records;
- the later chart only as a non-enrolled comparison.

Excluded:

- all incidents outside the accepted time window;
- profitability, robustness and strategy optimization;
- inaccessible platform internals;
- any execution state not represented by an admissible record;
- authentication of the synthetic exports by their named platforms.

## Evidence inventory

| Ref | Domain | Original filename or record ID | Source status | SHA-256 or immutable ID | Limitation |
| --- | --- | --- | --- | --- | --- |
| TV-01 | TradingView | Alert `A-77` | TRANSCRIBED | `A-77` | Synthetic source export |
| CFG-01 | Configuration | Enrolled revision `rev-a` | TRANSCRIBED | `rev-a` | Synthetic immutable snapshot |
| RX-01 | Receiver | Request `R-1001` | TRANSCRIBED | `R-1001` | Synthetic raw receipt |
| RX-02 | Receiver | Request `R-1002` | TRANSCRIBED | `R-1002` | Synthetic raw receipt |
| CN-01 | Connector | Client order `C-501` | TRANSCRIBED | `C-501` | Synthetic connector log |
| CN-02 | Connector | Client order `C-502` | TRANSCRIBED | `C-502` | Synthetic connector log |
| BR-01 | Broker | Broker order `BR-01` | TRANSCRIBED | `BR-01` | Synthetic broker log |
| BR-02 | Broker | Broker order `BR-02` | TRANSCRIBED | `BR-02` | Synthetic broker log |
| CH-01 | Later chart | Revision `rev-b` | TRANSCRIBED | `rev-b` | Not the enrolled revision |

Evidence not supplied:

| Missing domain or item | Effect on the audit |
| --- | --- |
| TradingView internal retry record | The resend mechanism is consistent with the records but is not directly authenticated by TradingView |
| Source export signatures | Platform authorship of the synthetic records is outside this demonstration |

No conclusion below relies on an item absent from this inventory.

## Configuration identity

| Configuration field | Enrolled value | Evidence ref | Verdict |
| --- | --- | --- | --- |
| Script name and revision | Synthetic strategy, `rev-a` | CFG-01 | PASS |
| Alert creation time | Before the accepted incident window | CFG-01 | PASS |
| Alert condition | Long, confirmed 15-minute close | CFG-01 | PASS |
| Message template | Contains stable event identity `evt-991` | CFG-01, TV-01 | PASS |
| Input settings | Frozen in the synthetic snapshot | CFG-01 | PASS |
| Symbol and venue | BTCUSDT, synthetic venue | CFG-01 | PASS |
| Timeframe | 15 minutes | CFG-01 | PASS |
| Chart type | Standard candles | CFG-01 | PASS |
| Strategy properties | Close-only calculation | CFG-01 | PASS |

Configuration verdict:

`CONFIGURATION_CONFIRMED`

CH-01 is not used as a substitute for the enrolled configuration because it
records revision `rev-b`, not `rev-a`.

## Clock normalization

| Domain | Raw timezone | Resolution | Clock source | Uncertainty | UTC normalization |
| --- | --- | --- | --- | --- | --- |
| TradingView | UTC | 1 ms | Synthetic platform clock | +/- 100 ms | None required |
| Receiver | UTC | 1 ms | Synthetic host clock | +/- 100 ms | None required |
| Connector | UTC | 1 ms | Synthetic host clock | +/- 100 ms | None required |
| Broker | UTC | 1 ms | Synthetic broker clock | +/- 100 ms | None required |

Ordering rule:

> Events are ordered only when their uncertainty intervals do not overlap.
> No material conclusion in this sample depends on the order of two records
> separated by 200 ms or less.

## Normalized chronology

| UTC time | Raw time | Evidence ref | Domain | Observed fact | Interpretation |
| --- | --- | --- | --- | --- | --- |
| 14:30:00.125 | 14:30:00.125Z | TV-01 | TradingView | Alert `A-77` recorded payload `evt-991` | One recorded originating event |
| 14:30:00.412 | 14:30:00.412Z | RX-01 | Receiver | Request `R-1001` received | Delivery attempt 1 |
| 14:30:00.590 | 14:30:00.590Z | CN-01 | Connector | Client order `C-501` submitted | First downstream submission |
| 14:30:00.810 | 14:30:00.810Z | BR-01 | Broker | `C-501` accepted | First broker order confirmed |
| 14:30:01.020 | 14:30:01.020Z | BR-01 | Broker | `C-501` filled | First fill confirmed |
| 14:30:05.438 | 14:30:05.438Z | RX-02 | Receiver | Identical payload received after first response 500 | Delivery attempt 2, consistent with resend |
| 14:30:05.601 | 14:30:05.601Z | CN-02 | Connector | Client order `C-502` submitted | Second downstream submission |
| 14:30:05.820 | 14:30:05.820Z | BR-02 | Broker | `C-502` accepted | Second broker order confirmed |
| 14:30:06.040 | 14:30:06.040Z | BR-02 | Broker | `C-502` filled | Second fill confirmed |

## Origin and delivery-attempt mapping

| Originating event | Attempt | Receiver request | Connector correlation | Broker client order | Broker order |
| --- | --- | --- | --- | --- | --- |
| `A-77` / `evt-991` | 1 | `R-1001` | `C-501` | `C-501` | `BR-01` |
| `A-77` / `evt-991` | 2 | `R-1002` | `C-502` | `C-502` | `BR-02` |

Mapping method:

> TV-01 records one alert ID and stable event identity. RX-01 and RX-02 retain
> separate request IDs, the same event identity and the same payload. The
> initial request records an HTTP 500 response, and the second request follows
> approximately five seconds later. These facts support one origin with two
> delivery attempts in this synthetic case.

## Stage matrix

| Stage question | Verdict | Evidence refs | Reason |
| --- | --- | --- | --- |
| Was the enrolled configuration identified? | PASS | CFG-01 | Revision and settings are frozen |
| Was the originating TradingView event identified? | PASS | TV-01 | One alert ID and event identity are recorded |
| Were all supplied delivery attempts preserved? | PASS | RX-01, RX-02 | Both request IDs remain distinct |
| Was retry identity distinguished from event identity? | PASS | TV-01, RX-01, RX-02 | Two attempts map to one recorded origin |
| Did the connector parse the intended payload? | PASS | CN-01, CN-02 | Both connector records reference the intended event |
| Did the connector submit the intended action exactly once? | FAIL | CN-01, CN-02 | Two client orders were submitted |
| Did the broker accept or reject the submission? | PASS | BR-01, BR-02 | Both client orders were accepted |
| Is each claimed fill supported by a broker record? | PASS | BR-01, BR-02 | Each fill has a broker record |
| Can the disputed outcome be localized to one stage? | PASS | RX-01, RX-02, CN-01, CN-02 | Duplicate execution begins at connector submission |

## Diagnosis adjudication

Customer's initial diagnosis:

> TradingView may have generated two signals, or the original signal may have
> repainted because the current chart no longer shows it.

Adjudication:

`REJECTED`

Evidence-linked reasoning:

1. One originating alert is recorded, while two delivery attempts are
   preserved - TV-01, RX-01, RX-02.
2. Each delivery attempt produced a different connector order - CN-01, CN-02.
3. Both connector orders were accepted and filled - BR-01, BR-02.

Narrow supported diagnosis:

> The connector did not enforce one-action idempotency across two delivery
> attempts associated with the same recorded originating event.

Alternative explanations not eliminated:

- TradingView's internal resend decision is not independently authenticated;
  a platform-side retry record would be needed to prove that internal step.
- The current chart cannot adjudicate repainting because CH-01 uses a different
  revision from CFG-01.

## Findings

| ID | Severity | Finding | Evidence refs | Consequence |
| --- | --- | --- | --- | --- |
| F-01 | HIGH | The connector submitted a new client order for each delivery attempt associated with one event identity | RX-01, RX-02, CN-01, CN-02 | Two broker orders were created instead of one |
| F-02 | MEDIUM | The current chart revision differs from the enrolled alert revision | CFG-01, CH-01 | The chart cannot adjudicate the original realtime signal |
| F-03 | INFORMATIONAL | Platform authorship and the internal retry decision are not cryptographically established | TV-01, RX-01, RX-02 | The report localizes the observed duplicate path but does not certify platform internals |

Severity describes the observed operational consequence, not trading
profitability or future risk probability.

## Corrective controls

| Priority | Control | Finding addressed | Verification evidence |
| --- | --- | --- | --- |
| 1 | Persist a stable event ID and reject or return the prior result for repeated delivery attempts | F-01 | A synthetic retry produces one broker submission and two retained receiver attempts |
| 2 | Store the enrolled script revision and settings beside every alert definition | F-02 | Incident export contains a configuration manifest matching the server-side alert |
| 3 | Retain raw request ID, response code and correlation fields for every attempt | F-01, F-03 | Audit export reconstructs origin, attempts and downstream actions without inference |

## Unresolved items

| Code | Unresolved question | Missing or ambiguous evidence | Effect |
| --- | --- | --- | --- |
| U-01 | Did TradingView itself initiate the second delivery? | Authenticated internal retry record | Internal resend mechanism remains unverified |
| U-02 | Would revision `rev-a` still display the original signal after recalculation? | Comparable chart export using the enrolled revision and settings | Repainting remains outside the supported diagnosis |

## Final boundary statement

This report establishes only what the listed synthetic records support for the
accepted incident window. Receipt of a webhook does not cryptographically
prove that TradingView authored it. A simulated strategy fill is not an actual
broker fill. Absence of a record does not prove absence of an event. The report
makes no claim about profitability, robustness, future performance or a
trading edge.

## Reviewer completion gate

| Check | PASS / FAIL |
| --- | --- |
| Every material claim cites an evidence ref | PASS |
| Every supplied record appears in the inventory | PASS |
| Raw observations are separated from interpretation | PASS |
| Delivery attempts are separated from originating events | PASS |
| Configuration identity is explicit | PASS |
| Clock uncertainty is explicit | PASS |
| Missing evidence is marked `NOT_VERIFIED` or unresolved | PASS |
| Broker fills are supported only by broker records | PASS |
| Scope and exclusions match the accepted synthetic question | PASS |
| Final report contains no credentials or unrelated account data | PASS |

Completion status: `READY_AS_SYNTHETIC_SAMPLE_ONLY`
