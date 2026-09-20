from __future__ import annotations

import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PINE = ROOT / "examples" / "pine"


class PublicEvidenceTests(unittest.TestCase):
    def test_pine_fixture_matches_manifest(self) -> None:
        manifest = PINE / "SHA256SUMS.txt"

        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, filename = line.split(" *", maxsplit=1)
            actual = hashlib.sha256((PINE / filename).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)

    def test_pine_pair_contains_the_declared_controlled_difference(self) -> None:
        clean = (PINE / "P01_clean_confirmed_htf.pine").read_text(encoding="utf-8")
        contaminated = (PINE / "P01_contaminated_future_htf.pine").read_text(
            encoding="utf-8"
        )

        self.assertIn("close[1]", clean)
        self.assertIn("barstate.isconfirmed", clean)
        self.assertNotIn("close[1]", contaminated)
        self.assertNotIn("barstate.isconfirmed and", contaminated)

    def test_pine_report_preserves_runtime_limits(self) -> None:
        report = (ROOT / "docs" / "PINE_AUDIT_SAMPLE_EN.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("NOT VERIFIED", report)
        self.assertIn("does not use a Pine parser", report)
        self.assertIn("P01_contaminated_future_htf.pine:16", report)

    def test_pine_fixture_readme_matches_runtime_record(self) -> None:
        readme = (PINE / "README.md").read_text(encoding="utf-8")

        self.assertIn("compiled and produced a", readme)
        self.assertIn("PINE_TRADINGVIEW_EXECUTION_2026-09-20.md", readme)
        self.assertIn("NOT VERIFIED", readme)

    def test_tradingview_record_is_public_but_bounded(self) -> None:
        manifest = (ROOT / "docs" / "PUBLIC_RELEASE_MANIFEST.txt").read_text(
            encoding="utf-8"
        )
        record = (
            ROOT / "docs" / "PINE_TRADINGVIEW_EXECUTION_2026-09-20.md"
        ).read_text(encoding="utf-8")

        self.assertIn("docs/PINE_TRADINGVIEW_EXECUTION_2026-09-20.md", manifest)
        self.assertIn("not evidence", record)
        self.assertIn("NOT VERIFIED", record)
        self.assertIn("No trade was placed", record)


if __name__ == "__main__":
    unittest.main()
