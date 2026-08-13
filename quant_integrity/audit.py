from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
import string
from typing import Iterable


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    source: str
    row: int | None = None


@dataclass(frozen=True)
class ContractLife:
    symbol: str
    life_id: str
    life_start: datetime
    cessation_at: datetime | None


@dataclass(frozen=True)
class AuditReport:
    status: str
    lives_checked: int
    market_rows_checked: int
    signal_rows_checked: int
    manifest_entries_checked: int
    error_count: int
    warning_count: int
    issues: tuple[Issue, ...]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["issues"] = [asdict(issue) for issue in self.issues]
        return payload


class SchemaError(ValueError):
    pass


def _parse_timestamp(value: str, *, field: str) -> datetime:
    text = value.strip()
    if not text:
        raise SchemaError(f"missing timestamp in {field}")
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise SchemaError(f"invalid timestamp in {field}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise SchemaError(f"timezone required in {field}: {value!r}")
    return parsed.astimezone(timezone.utc)


def _parse_optional_timestamp(value: str, *, field: str) -> datetime | None:
    if not value.strip():
        return None
    return _parse_timestamp(value, field=field)


def _parse_decimal(value: str, *, field: str) -> Decimal:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise SchemaError(f"invalid decimal in {field}: {value!r}") from exc
    if not number.is_finite():
        raise SchemaError(f"non-finite decimal in {field}: {value!r}")
    return number


def _read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        missing = required - fields
        if missing:
            raise SchemaError(f"{path}: missing columns {sorted(missing)}")
        return [dict(row) for row in reader]


def _load_lives(path: Path) -> tuple[dict[tuple[str, str], ContractLife], list[Issue]]:
    rows = _read_csv(path, {"symbol", "life_id", "life_start", "cessation_at"})
    lives: dict[tuple[str, str], ContractLife] = {}
    issues: list[Issue] = []
    by_symbol: dict[str, list[ContractLife]] = {}

    for row_number, row in enumerate(rows, start=2):
        key = (row["symbol"].strip(), row["life_id"].strip())
        if not all(key):
            raise SchemaError(f"{path}:{row_number}: empty symbol or life_id")
        life = ContractLife(
            symbol=key[0],
            life_id=key[1],
            life_start=_parse_timestamp(row["life_start"], field="life_start"),
            cessation_at=_parse_optional_timestamp(row["cessation_at"], field="cessation_at"),
        )
        if life.cessation_at is not None and life.cessation_at <= life.life_start:
            issues.append(
                Issue("ERROR", "INVALID_LIFE_INTERVAL", "cessation_at must follow life_start", str(path), row_number)
            )
        if key in lives:
            issues.append(Issue("ERROR", "DUPLICATE_LIFE_KEY", f"duplicate life key {key}", str(path), row_number))
            continue
        lives[key] = life
        by_symbol.setdefault(life.symbol, []).append(life)

    for symbol, symbol_lives in by_symbol.items():
        ordered = sorted(symbol_lives, key=lambda item: item.life_start)
        for previous, current in zip(ordered, ordered[1:]):
            if previous.cessation_at is None or current.life_start <= previous.cessation_at:
                issues.append(
                    Issue(
                        "ERROR",
                        "OVERLAPPING_LIVES",
                        f"{symbol} lives {previous.life_id} and {current.life_id} overlap",
                        str(path),
                    )
                )
    return lives, issues


def _audit_market(path: Path, lives: dict[tuple[str, str], ContractLife]) -> tuple[int, list[Issue]]:
    required = {"symbol", "life_id", "timestamp", "open", "high", "low", "close", "volume"}
    rows = _read_csv(path, required)
    issues: list[Issue] = []
    seen: set[tuple[str, str, datetime]] = set()

    for row_number, row in enumerate(rows, start=2):
        key = (row["symbol"].strip(), row["life_id"].strip())
        timestamp = _parse_timestamp(row["timestamp"], field="timestamp")
        prices = [_parse_decimal(row[name], field=name) for name in ("open", "high", "low", "close")]
        open_price, high, low, close = prices
        volume = _parse_decimal(row["volume"], field="volume")
        identity = (*key, timestamp)
        if identity in seen:
            issues.append(Issue("ERROR", "DUPLICATE_MARKET_ROW", f"duplicate market row {identity}", str(path), row_number))
        seen.add(identity)

        if any(price <= 0 for price in prices):
            issues.append(Issue("ERROR", "NON_POSITIVE_PRICE", f"non-positive OHLC value for {key}", str(path), row_number))
        if volume < 0:
            issues.append(Issue("ERROR", "NEGATIVE_VOLUME", f"negative volume for {key}", str(path), row_number))
        if high < max(open_price, low, close) or low > min(open_price, high, close):
            issues.append(Issue("ERROR", "INVALID_OHLC_BOUNDS", f"inconsistent OHLC bounds for {key}", str(path), row_number))

        life = lives.get(key)
        if life is None:
            issues.append(Issue("ERROR", "UNMAPPED_LIFE", f"market row references unknown life {key}", str(path), row_number))
            continue
        if timestamp < life.life_start:
            issues.append(Issue("ERROR", "BEFORE_LIFE_START", f"market row predates {key}", str(path), row_number))
        if life.cessation_at is None or timestamp <= life.cessation_at:
            continue

        if len(set(prices)) == 1 and volume == 0:
            code = "PHANTOM_POST_CESSATION_ROW"
            message = f"flat zero-volume row exists after cessation of {key}"
        else:
            code = "ACTIVE_POST_CESSATION_ROW"
            message = f"non-empty market activity exists after cessation of {key}"
        issues.append(Issue("ERROR", code, message, str(path), row_number))
    return len(rows), issues


def _audit_signals(path: Path, lives: dict[tuple[str, str], ContractLife]) -> tuple[int, list[Issue]]:
    required = {"symbol", "life_id", "feature_end_at", "decision_at", "execution_at"}
    rows = _read_csv(path, required)
    issues: list[Issue] = []

    for row_number, row in enumerate(rows, start=2):
        key = (row["symbol"].strip(), row["life_id"].strip())
        feature_end = _parse_timestamp(row["feature_end_at"], field="feature_end_at")
        decision = _parse_timestamp(row["decision_at"], field="decision_at")
        execution = _parse_timestamp(row["execution_at"], field="execution_at")
        life = lives.get(key)

        if feature_end > decision:
            issues.append(Issue("ERROR", "LOOKAHEAD", "feature data ends after the decision time", str(path), row_number))
        if execution < decision:
            issues.append(Issue("ERROR", "EXECUTION_PRECEDES_DECISION", "execution precedes decision", str(path), row_number))
        if life is None:
            issues.append(Issue("ERROR", "UNMAPPED_SIGNAL_LIFE", f"signal references unknown life {key}", str(path), row_number))
            continue
        if feature_end < life.life_start:
            issues.append(Issue("ERROR", "FEATURE_BEFORE_LIFE_START", f"feature predates {key}", str(path), row_number))
        if decision < life.life_start:
            issues.append(Issue("ERROR", "DECISION_BEFORE_LIFE_START", f"decision predates {key}", str(path), row_number))
        if execution < life.life_start:
            issues.append(Issue("ERROR", "EXECUTION_BEFORE_LIFE_START", f"execution predates {key}", str(path), row_number))
        if life.cessation_at is not None and execution > life.cessation_at:
            issues.append(Issue("ERROR", "EXECUTION_AFTER_CESSATION", f"execution follows cessation of {key}", str(path), row_number))
    return len(rows), issues


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit_manifest(path: Path) -> tuple[int, list[Issue]]:
    issues: list[Issue] = []
    checked = 0
    base = path.parent.resolve()
    for row_number, raw_line in enumerate(path.read_text(encoding="ascii").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        expected = parts[0] if parts else ""
        if len(parts) != 2 or len(expected) != 64 or any(character not in string.hexdigits for character in expected):
            issues.append(Issue("ERROR", "INVALID_MANIFEST_LINE", "expected SHA256 and relative path", str(path), row_number))
            continue
        expected, relative = parts
        relative = relative.lstrip("*")
        target = (base / relative).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            issues.append(Issue("ERROR", "MANIFEST_PATH_ESCAPE", relative, str(path), row_number))
            continue
        if not target.is_file():
            issues.append(Issue("ERROR", "MANIFEST_FILE_MISSING", relative, str(path), row_number))
            continue
        checked += 1
        actual = _sha256(target)
        if actual.lower() != expected.lower():
            issues.append(Issue("ERROR", "CHECKSUM_MISMATCH", relative, str(path), row_number))
    return checked, issues


def _counts(issues: Iterable[Issue]) -> tuple[int, int]:
    materialized = tuple(issues)
    return (
        sum(issue.severity == "ERROR" for issue in materialized),
        sum(issue.severity == "WARNING" for issue in materialized),
    )


def audit_files(
    *,
    lives_path: Path,
    market_path: Path,
    signals_path: Path,
    manifest_path: Path | None = None,
) -> AuditReport:
    lives, issues = _load_lives(lives_path)
    market_count, market_issues = _audit_market(market_path, lives)
    signal_count, signal_issues = _audit_signals(signals_path, lives)
    issues.extend(market_issues)
    issues.extend(signal_issues)
    manifest_count = 0
    if manifest_path is not None:
        manifest_count, manifest_issues = _audit_manifest(manifest_path)
        issues.extend(manifest_issues)
    errors, warnings = _counts(issues)
    return AuditReport(
        status="PASS" if errors == 0 else "FAIL",
        lives_checked=len(lives),
        market_rows_checked=market_count,
        signal_rows_checked=signal_count,
        manifest_entries_checked=manifest_count,
        error_count=errors,
        warning_count=warnings,
        issues=tuple(issues),
    )
