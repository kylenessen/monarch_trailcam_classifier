import json
from pathlib import Path
import tempfile
import unittest

from prepare_deployment import prepare_configuration, prepare_file


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.records = {"SC1_20231117114501.JPG": {
            "confirmed": True, "notes": "Original note", "user": "observer",
            "cells": {"cell_0_1": {"count": "10-99", "sunlight": True}}
        }}

    def test_legacy_requires_explicit_grid(self):
        with self.assertRaisesRegex(ValueError, "--rows"):
            prepare_configuration(self.records)

    def test_preserves_annotation_fields_and_normalizes_sunlight(self):
        original = json.dumps(self.records)
        result = prepare_configuration(self.records, 9, 16)
        record = result["classifications"][next(iter(self.records))]
        self.assertEqual(record["notes"], "Original note")
        self.assertTrue(record["confirmed"])
        self.assertTrue(record["cells"]["cell_0_1"]["directSun"])
        self.assertTrue(record["cells"]["cell_0_1"]["sunlight"])
        self.assertEqual(json.dumps(self.records), original)

    def test_rejects_grid_that_would_misplace_cells(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            prepare_configuration(self.records, 1, 1)

    def test_modern_records_round_trip_without_changes(self):
        data = {"rows": 9, "columns": 16, "classifications": {
            "image.JPG": {"cells": {"cell_0_0": {"count": "1-9", "directSun": False}}}
        }}
        self.assertEqual(prepare_configuration(data), data)
        with self.assertRaisesRegex(ValueError, "already stored"):
            prepare_configuration(data, 18, 32)

    def test_existing_destination_and_source_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "SC1.json"
            target = Path(directory) / "configurations.json"
            source.write_text(json.dumps(self.records))
            before = source.read_bytes()
            prepare_file(source, target, 9, 16)
            with self.assertRaises(FileExistsError):
                prepare_file(source, target, 9, 16)
            with self.assertRaises(FileExistsError):
                prepare_file(source, source, 9, 16)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
