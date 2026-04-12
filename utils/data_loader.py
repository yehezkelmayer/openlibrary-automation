"""Data loader utility for test data."""
import json
import yaml
from pathlib import Path
from typing import Any


class DataLoader:
    """Utility class for loading test data from files."""

    def __init__(self, data_dir: str = "data"):
        """Initialize DataLoader with data directory path."""
        self.data_dir = Path(data_dir)

    def load_yaml(self, filename: str) -> dict:
        """Load data from YAML file."""
        filepath = self.data_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_json(self, filename: str) -> dict:
        """Load data from JSON file."""
        filepath = self.data_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_search_test_data(self) -> list[dict]:
        """Get search test data."""
        data = self.load_yaml("test_data.yaml")
        return data.get("search_tests", [])

    def get_performance_thresholds(self) -> dict:
        """Get performance threshold data."""
        data = self.load_yaml("test_data.yaml")
        return data.get("performance_thresholds", {})

    def get_reading_list_statuses(self) -> list[str]:
        """Get available reading list statuses."""
        data = self.load_yaml("test_data.yaml")
        return data.get("reading_list_statuses", [])


def load_test_data() -> dict:
    """Load all test data."""
    loader = DataLoader()
    return loader.load_yaml("test_data.yaml")
