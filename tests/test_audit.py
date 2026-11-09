from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from quant_integrity.audit import SchemaError, audit_files
from quant_integrity.cli import main


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

    def run_cli(self, inputs: tuple[Path, Path, Path], *extra: str) -> tuple[int, dict]:
        args = [part for name, path in zip(("--lives", "--market", "--signals"), inputs)
                for part in (name, str(path))]
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main([*args, *extra])
        return code, json.loads(stdout.getvalue())

    def test_cli_does_not_overwrite_input_or_existing_report(self) -> None:
        inputs = self.clean_inputs()
        existing_report = self.write("report.json", '{"kept":true}\n')
        for path in (*inputs, existing_report):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                code, payload = self.run_cli(inputs, "--json-out", str(path))
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(code, 3)
                self.assertEqual(payload["status"], "ERROR")

    def test_cli_writes_new_report_without_changing_stdout(self) -> None:
        inputs = self.clean_inputs()
        target = self.root / "new" / "report.json"
        code, payload = self.run_cli(inputs, "--json-out", str(target))
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), payload)

    def test_cli_reports_invalid_encoding_and_unterminated_csv(self) -> None:
        inputs = self.clean_inputs()
        for data in (
            b"\xff",
            (MARKET_HEADER.rstrip("\n") + ",note\n"
             "ABCUSDT,life-1,2024-01-02T00:00:00Z,10,12,9,11,1,\"unterminated\n").encode("utf-8"),
        ):
            with self.subTest(data=data):
                inputs[1].write_bytes(data)
                code, payload = self.run_cli(inputs)
                self.assertEqual(code, 3)
                self.assertEqual(payload["status"], "ERROR")

    def test_cli_rejects_each_header_only_input(self) -> None:
        for index, name in enumerate(("lives.csv", "market.csv", "signals.csv")):
            with self.subTest(filename=name):
                inputs = self.clean_inputs()
                header = inputs[index].read_bytes().splitlines(keepends=True)[0]
                inputs[index].write_bytes(header + b"\r\n")
                code, payload = self.run_cli(inputs)
                self.assertEqual(code, 3)
                self.assertEqual(payload["status"], "ERROR")
                self.assertIn(f"{name}: no data rows to audit", payload["message"])

    def test_cli_reports_utc_underflow_and_overflow_without_a_traceback(self) -> None:
        inputs = self.clean_inputs()
        for value in ("0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"):
            with self.subTest(timestamp=value):
                self.write("lives.csv", LIVES_HEADER + f"ABCUSDT,life-1,{value},\n")
                code, payload = self.run_cli(inputs)
                self.assertEqual(code, 3)
                self.assertEqual(payload["status"], "ERROR")
                self.assertIn("life_start: outside supported UTC range", payload["message"])

    def test_error_references_physical_record_line_after_multiline_and_blank_rows(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            MARKET_HEADER.rstrip("\n") + ",note\n"
            'ABCUSDT,life-1,2024-01-02T00:00:00Z,10,12,9,11,1,"two\nlines"\n'
            '\nABCUSDT,life-1,2024-01-02T01:00:00Z,10,12,9,11,-1,invalid\n',
            encoding="utf-8",
        )
        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)
        issue, = report.issues
        self.assertEqual((issue.code, issue.row), ("NEGATIVE_VOLUME", 5))

    def test_comments_only_manifest_cannot_pass(self) -> None:
        lives, market, signals = self.clean_inputs()
        manifest = self.write("SHA256SUMS.txt", "# No checksums in this export\n\n")
        report = audit_files(lives_path=lives, market_path=market, signals_path=signals,
                             manifest_path=manifest)
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.manifest_entries_checked, 0)
        self.assertEqual([issue.code for issue in report.issues], ["EMPTY_MANIFEST"])

    def test_same_market_instant_in_two_timezones_is_a_duplicate(self) -> None:
        lives, market, signals = self.clean_inputs()
        market.write_text(
            MARKET_HEADER
            + "ABCUSDT,life-1,2024-01-02T00:00:00Z,10,12,9,11,1\n"
            + "ABCUSDT,life-1,2024-01-02T01:00:00+01:00,10,12,9,11,1\n",
            encoding="utf-8",
        )
        report = audit_files(lives_path=lives, market_path=market, signals_path=signals)
        self.assertEqual([issue.code for issue in report.issues], ["DUPLICATE_MARKET_ROW"])

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
