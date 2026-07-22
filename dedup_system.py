import sqlite3
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ValidationResult:
    classification: str
    reason: str
    added: bool


class DataRedundancyRemovalSystem:
    """Validate incoming data and append only unique entries to a cloud DB."""

    FALSE_POSITIVE_VALUES = {
        "",
        "n/a",
        "na",
        "none",
        "null",
        "false",
        "dummy",
        "test",
    }

    def __init__(self, db_path: str = "cloud_data.db") -> None:
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cloud_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_data TEXT NOT NULL,
                normalized_data TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cloud_data_normalized ON cloud_data(normalized_data)"
        )
        self.connection.commit()

    @staticmethod
    def normalize(data: str) -> str:
        return " ".join(str(data).strip().lower().split())

    def _is_false_positive(self, normalized_data: str) -> bool:
        return normalized_data in self.FALSE_POSITIVE_VALUES or len(normalized_data) < 3

    def classify(self, data: str) -> str:
        normalized = self.normalize(data)
        if self._is_false_positive(normalized):
            return "false_positive"
        if self._is_redundant(normalized):
            return "redundant"
        return "unique"

    def _is_redundant(self, normalized_data: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM cloud_data WHERE normalized_data = ? LIMIT 1",
            (normalized_data,),
        ).fetchone()
        return row is not None

    def validate_and_append(self, data: str) -> ValidationResult:
        normalized = self.normalize(data)

        if self._is_false_positive(normalized):
            return ValidationResult(
                classification="false_positive",
                reason="Entry is invalid or too short.",
                added=False,
            )

        if self._is_redundant(normalized):
            return ValidationResult(
                classification="redundant",
                reason="Duplicate entry already exists in cloud database.",
                added=False,
            )

        self.connection.execute(
            "INSERT INTO cloud_data(raw_data, normalized_data) VALUES (?, ?)",
            (str(data).strip(), normalized),
        )
        self.connection.commit()
        return ValidationResult(
            classification="unique",
            reason="Entry validated and appended to cloud database.",
            added=True,
        )

    def process_batch(self, entries: Iterable[str]) -> dict[str, int]:
        summary = {"unique": 0, "redundant": 0, "false_positive": 0}
        for entry in entries:
            result = self.validate_and_append(entry)
            summary[result.classification] += 1
        return summary

    def count_entries(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM cloud_data").fetchone()
        return int(row[0])

    def close(self) -> None:
        self.connection.close()


if __name__ == "__main__":
    system = DataRedundancyRemovalSystem()
    print(system.validate_and_append("Alice"))
    print(system.validate_and_append(" alice "))
    print(system.validate_and_append("N/A"))
    system.close()
