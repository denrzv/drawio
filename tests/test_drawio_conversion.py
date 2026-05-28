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

                    generated_dsl = Path(output_dir, "workspace.dsl").read_text(encoding="utf-8")
                    expected_dsl = (EXPECTED_DIR / case["expected"]).read_text(encoding="utf-8")
                    self.assertEqual(expected_dsl, generated_dsl)


if __name__ == "__main__":
    unittest.main()
