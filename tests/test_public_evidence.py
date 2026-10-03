from __future__ import annotations

import hashlib
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PINE = ROOT / "examples" / "pine"
INCIDENT_SOURCE = (
    ROOT / "docs" / "TRADINGVIEW_INCIDENT_AUDIT_SAMPLE_REPORT_2026-10-01.md"
)
INCIDENT_PDF = (
    ROOT / "public_demo" / "TRADINGVIEW_INCIDENT_AUDIT_SAMPLE_REPORT_2026-10-01.pdf"
)


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

    def test_incident_sample_is_frozen_and_bounded(self) -> None:
        report = INCIDENT_SOURCE.read_text(encoding="utf-8")

        self.assertEqual(
            hashlib.sha256(INCIDENT_SOURCE.read_bytes()).hexdigest(),
            "fc5188795bc257326d59771f85c707c476b0849b381ca835309ca2c1679a9000",
        )
        self.assertEqual(
            hashlib.sha256(INCIDENT_PDF.read_bytes()).hexdigest(),
            "a2c1f2cc7ce899b1bceefba7cd991849426b047b5f6bf3fc747a408dc71bd10c",
        )
        self.assertIn("SYNTHETIC_SAMPLE_NOT_A_CUSTOMER_AUDIT", report)
        self.assertIn("does not cryptographically", report)
        self.assertIn("makes no claim about profitability", report)


if __name__ == "__main__":
    unittest.main()
