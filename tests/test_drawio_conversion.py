import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from drawio_parser import Element, apply_marker_tags, export_to_dsl, marker_config


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


    def test_marker_tags_and_styles_are_generated_without_overwriting_existing_tags(self):
        crm = Element({
            "id": "crm",
            "c4Type": "Software System",
            "c4Name": "CRM",
            "changeStatus": "created",
            "c4Tags": "ExistingTag",
        })
        api = Element({
            "id": "api",
            "c4Type": "Container",
            "c4Name": "Themes BFF",
            "c4Description": "Provides themes for operator",
            "c4Technology": "Spring Boot",
            "changeStatus": "changed",
        })
        crm.left_top = [0, 0]
        crm.right_bottom = [400, 300]
        api.left_top = [10, 10]
        api.right_bottom = [100, 100]
        api.parent_id = "crm"
        components = {"crm": crm, "api": api}

        apply_marker_tags(components, marker_config(enabled=True))

        with tempfile.TemporaryDirectory() as output_dir:
            previous_cwd = os.getcwd()
            try:
                os.chdir(output_dir)
                export_to_dsl(components, [])
                generated_dsl = Path("workspace.dsl").read_text(encoding="utf-8")
            finally:
                os.chdir(previous_cwd)

        self.assertIn('tags "ExistingTag,Marker:Red"', generated_dsl)
        self.assertIn('tags "Marker:Green"', generated_dsl)
        self.assertIn('element "Marker:Green" {', generated_dsl)
        self.assertIn('icon ./assets/structurizr/icons/markers/marker-green.svg', generated_dsl)
        for marker_color in ('green', 'red', 'blue', 'gray', 'purple'):
            marker_tag = marker_color.title()
            self.assertIn(f'element "Marker:{marker_tag}" {{', generated_dsl)
            self.assertIn(f'icon ./assets/structurizr/icons/markers/marker-{marker_color}.svg', generated_dsl)

    def test_marker_tags_remain_disabled_by_default(self):
        component = Element({
            "id": "crm",
            "c4Type": "Software System",
            "c4Name": "CRM",
            "changeStatus": "created",
        })

        apply_marker_tags({"crm": component}, marker_config())

        self.assertFalse(hasattr(component, "marker_tag"))

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
