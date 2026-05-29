import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIR = REPO_ROOT / "tests" / "fixtures" / "expected"


class DrawioConversionTest(unittest.TestCase):
    def test_repository_diagrams_convert_to_structurizr_dsl(self):
        cases = [
            {
                "diagram": "system_context.drawio",
                "expected": "system_context.dsl",
                "stats": [
                    "Number of components: 4",
                    "Number of relations: 3",
                    "Number of broken relations: 0",
                ],
            },
            {
                "diagram": "container.drawio",
                "expected": "container.dsl",
                "stats": [
                    "Number of components: 7",
                    "Number of relations: 4",
                    "Number of broken relations: 0",
                ],
            },
        ]

        for case in cases:
            with self.subTest(diagram=case["diagram"]):
                with tempfile.TemporaryDirectory() as output_dir:
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(REPO_ROOT / "drawio_parser.py"),
                            "-i",
                            str(REPO_ROOT / case["diagram"]),
                            "-d",
                            "-s",
                        ],
                        cwd=output_dir,
                        check=True,
                        capture_output=True,
                        text=True,
                    )

                    for expected_stat in case["stats"]:
                        self.assertIn(expected_stat, result.stdout)

                    self.assertIn("Exported elements:", result.stdout)
                    self.assertIn("Exported relationships:", result.stdout)
                    self.assertIn("  - Software System: CRM", result.stdout)

                    generated_dsl = Path(output_dir, "workspace.dsl").read_text(encoding="utf-8")
                    expected_dsl = (EXPECTED_DIR / case["expected"]).read_text(encoding="utf-8")
                    self.assertEqual(expected_dsl, generated_dsl)

    def test_multiple_diagrams_convert_to_hierarchical_structurizr_dsl(self):
        with tempfile.TemporaryDirectory() as output_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "drawio_parser.py"),
                    "-i",
                    str(REPO_ROOT / "system_context.drawio"),
                    "-i",
                    str(REPO_ROOT / "container.drawio"),
                    "-H",
                    "-d",
                    "-s",
                ],
                cwd=output_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            for expected_stat in [
                "Number of components: 4",
                "Number of relations: 3",
                "Number of broken relations: 0",
                "Number of components: 7",
                "Number of relations: 4",
            ]:
                self.assertIn(expected_stat, result.stdout)

            for expected_summary_line in [
                "Exported elements:",
                "  - Software System: CRM",
                "    - Container: agent-ui",
                "Exported relationships:",
                "  - Contact Center Agent -> CRM / agent-ui: Handles calls",
            ]:
                self.assertIn(expected_summary_line, result.stdout)

            expected_root = EXPECTED_DIR / "hierarchical"
            for expected_file in expected_root.rglob("*.dsl"):
                generated_file = Path(output_dir, expected_file.relative_to(expected_root))
                self.assertTrue(generated_file.exists(), f"Missing generated file: {generated_file}")
                self.assertEqual(
                    expected_file.read_text(encoding="utf-8"),
                    generated_file.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
