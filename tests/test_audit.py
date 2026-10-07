from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from quant_integrity.audit import SchemaError, audit_files


LIVES_HEADER = "symbol,life_id,life_start,cessation_at\n"
MARKET_HEADER = "symbol,life_id,timestamp,open,high,low,close,volume\n"
SIGNALS_HEADER = "symbol,life_id,feature_end_at,decision_at,execution_at\n"


class IntegrityAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def clean_inputs(self) -> tuple[Path, Path, Path]:
        lives = self.write(
            "lives.csv",
            LIVES_HEADER
            + "ABCUSDT,life-1,2024-01-01T00:00:00Z,2024-01-03T09:00:00Z\n"
            + "ABCUSDT,life-2,2024-02-01T00:00:00Z,\n",
        )
        market = self.write(
            "market.csv",
            MARKET_HEADER
            + "ABCUSDT,life-1,2024-01-02T00:00:00Z,10,12,9,11,2500\n"
            + "ABCUSDT,life-2,2024-02-02T00:00:00Z,20,22,19,21,3100\n",
        )
        signals = self.write(
            "signals.csv",
            SIGNALS_HEADER
            + "ABCUSDT,life-1,2024-01-02T10:00:00Z,2024-01-02T10:00:00Z,2024-01-02T10:05:00Z\n",
        )
        return lives, market, signals

    def test_clean_point_in_time_dataset_passes(self) -> None:
        lives, market, signals = self.clean_inputs()

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)

        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.lives_checked, 2)
        self.assertEqual(report.error_count, 0)

    def test_lookahead_and_phantom_post_cessation_row_fail(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            market.read_text(encoding="utf-8")
            + "ABCUSDT,life-1,2024-01-04T00:00:00Z,11,11,11,11,0\n",
            encoding="utf-8",
        )
        signals.write_text(
            SIGNALS_HEADER
            + "ABCUSDT,life-1,2024-01-02T12:00:00Z,2024-01-02T11:00:00Z,2024-01-02T11:05:00Z\n",
            encoding="utf-8",
        )

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)
        codes = {issue.code for issue in report.issues}

        self.assertEqual(report.status, "FAIL")
        self.assertIn("LOOKAHEAD", codes)
        self.assertIn("PHANTOM_POST_CESSATION_ROW", codes)

    def test_non_empty_activity_after_cessation_is_distinct(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            market.read_text(encoding="utf-8")
            + "ABCUSDT,life-1,2024-01-04T00:00:00Z,11,12,10,11.5,25\n",
            encoding="utf-8",
        )

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)

        self.assertIn("ACTIVE_POST_CESSATION_ROW", {issue.code for issue in report.issues})

    def test_invalid_ohlc_and_negative_volume_are_rejected(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            MARKET_HEADER + "ABCUSDT,life-1,2024-01-02T00:00:00Z,10,9,11,12,-1\n",
            encoding="utf-8",
        )

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)
        codes = {issue.code for issue in report.issues}

        self.assertIn("INVALID_OHLC_BOUNDS", codes)
        self.assertIn("NEGATIVE_VOLUME", codes)

    def test_signal_cannot_execute_outside_contract_life(self) -> None:
        lives, market, signals = self.clean_inputs()
        signals.write_text(
            SIGNALS_HEADER
            + "ABCUSDT,life-1,2024-01-03T08:00:00Z,2024-01-03T08:30:00Z,2024-01-03T10:00:00Z\n",
            encoding="utf-8",
        )

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)

        self.assertIn("EXECUTION_AFTER_CESSATION", {issue.code for issue in report.issues})

    def test_relisted_lives_must_not_overlap(self) -> None:
        lives, market, signals = self.clean_inputs()
        lives.write_text(
            LIVES_HEADER
            + "ABCUSDT,life-1,2024-01-01T00:00:00Z,2024-03-01T00:00:00Z\n"
            + "ABCUSDT,life-2,2024-02-01T00:00:00Z,\n",
            encoding="utf-8",
        )

        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)

        self.assertIn("OVERLAPPING_LIVES", {issue.code for issue in report.issues})

    def test_matching_checksum_manifest_passes(self) -> None:
        lives, market, signals = self.clean_inputs()
        digest = hashlib.sha256(market.read_bytes()).hexdigest()
        manifest = self.write("SHA256SUMS.txt", f"{digest} *market.csv\n")

        report = audit_files(
            lives_path=lives,
            market_path=market,
            signals_path=signals,
            manifest_path=manifest,
        )

        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.manifest_entries_checked, 1)

    def test_changed_file_fails_checksum(self) -> None:
        lives, market, signals = self.clean_inputs()
        digest = hashlib.sha256(market.read_bytes()).hexdigest()
        manifest = self.write("SHA256SUMS.txt", f"{digest} *market.csv\n")
        market.write_text(market.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        report = audit_files(
            lives_path=lives,
            market_path=market,
            signals_path=signals,
            manifest_path=manifest,
        )

        self.assertIn("CHECKSUM_MISMATCH", {issue.code for issue in report.issues})

    def test_manifest_cannot_escape_its_directory(self) -> None:
        lives, market, signals = self.clean_inputs()
        manifest = self.write("SHA256SUMS.txt", f"{'0' * 64} *..\\outside.csv\n")

        report = audit_files(
            lives_path=lives,
            market_path=market,
            signals_path=signals,
            manifest_path=manifest,
        )

        self.assertIn("MANIFEST_PATH_ESCAPE", {issue.code for issue in report.issues})

    def test_manifest_hash_must_be_hexadecimal(self) -> None:
        lives, market, signals = self.clean_inputs()
        manifest = self.write("SHA256SUMS.txt", f"{'z' * 64} *market.csv\n")

        report = audit_files(
            lives_path=lives,
            market_path=market,
            signals_path=signals,
            manifest_path=manifest,
        )

        self.assertIn("INVALID_MANIFEST_LINE", {issue.code for issue in report.issues})

    def test_timezone_is_required(self) -> None:
        lives, market, signals = self.clean_inputs()
        lives.write_text(
            LIVES_HEADER + "ABCUSDT,life-1,2024-01-01T00:00:00,2024-01-03T09:00:00Z\n",
            encoding="utf-8",
        )

        with self.assertRaises(SchemaError):
            audit_files(lives_path=lives, market_path=market, signals_path=signals)

    def test_duplicate_csv_header_is_rejected(self) -> None:
        lives, market, signals = self.clean_inputs()
        lives.write_text(
            "symbol,symbol,life_id,life_start,cessation_at\n"
            "ABCUSDT,ABCUSDT,life-1,2024-01-01T00:00:00Z,2024-01-03T09:00:00Z\n",
            encoding="utf-8",
        )

        with self.assertRaises(SchemaError):
            audit_files(lives_path=lives, market_path=market, signals_path=signals)

    def test_incomplete_csv_row_is_rejected(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            MARKET_HEADER + "ABCUSDT,life-1,2024-01-02T00:00:00Z,10,12,9,11\n",
            encoding="utf-8",
        )

        with self.assertRaises(SchemaError):
            audit_files(lives_path=lives, market_path=market, signals_path=signals)

    def test_extra_csv_field_is_rejected(self) -> None:
        lives, market, signals = self.clean_inputs()
        signals.write_text(
            SIGNALS_HEADER
            + "ABCUSDT,life-1,2024-01-02T10:00:00Z,2024-01-02T10:00:00Z,2024-01-02T10:05:00Z,unexpected\n",
            encoding="utf-8",
        )

        with self.assertRaises(SchemaError):
            audit_files(lives_path=lives, market_path=market, signals_path=signals)

    def test_committed_clean_fixture_and_manifest_pass(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "examples" / "clean"

        report = audit_files(
            lives_path=fixture / "lives.csv",
            market_path=fixture / "market.csv",
            signals_path=fixture / "signals.csv",
            manifest_path=fixture / "SHA256SUMS.txt",
        )

        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.manifest_entries_checked, 3)

    def test_committed_contaminated_fixture_has_only_expected_findings(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "examples"

        report = audit_files(
            lives_path=fixture / "lives.csv",
            market_path=fixture / "market.csv",
            signals_path=fixture / "signals.csv",
            manifest_path=fixture / "SHA256SUMS.txt",
        )

        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.error_count, 2)
        self.assertEqual(
            {issue.code for issue in report.issues},
            {"LOOKAHEAD", "PHANTOM_POST_CESSATION_ROW"},
        )


if __name__ == "__main__":
    unittest.main()
