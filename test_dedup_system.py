import os
import tempfile
import unittest

from dedup_system import DataRedundancyRemovalSystem


class DataRedundancyRemovalSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.db_path = tempfile.mkstemp()
        os.close(fd)
        self.system = DataRedundancyRemovalSystem(self.db_path)

    def tearDown(self) -> None:
        self.system.close()
        os.remove(self.db_path)

    def test_unique_verified_data_is_added(self) -> None:
        result = self.system.validate_and_append("Customer-123")
        self.assertEqual(result.classification, "unique")
        self.assertTrue(result.added)
        self.assertEqual(self.system.count_entries(), 1)

    def test_redundant_data_is_not_added(self) -> None:
        self.system.validate_and_append("Alice Smith")
        duplicate = self.system.validate_and_append("  alice   smith ")

        self.assertEqual(duplicate.classification, "redundant")
        self.assertFalse(duplicate.added)
        self.assertEqual(self.system.count_entries(), 1)

    def test_false_positive_data_is_not_added(self) -> None:
        invalid = self.system.validate_and_append("N/A")
        too_short = self.system.validate_and_append("ok")

        self.assertEqual(invalid.classification, "false_positive")
        self.assertEqual(too_short.classification, "false_positive")
        self.assertEqual(self.system.count_entries(), 0)

    def test_batch_processing_classifies_entries(self) -> None:
        summary = self.system.process_batch(["Alpha", "alpha", "", "Beta"])

        self.assertEqual(summary, {"unique": 2, "redundant": 1, "false_positive": 1})
        self.assertEqual(self.system.count_entries(), 2)


if __name__ == "__main__":
    unittest.main()
