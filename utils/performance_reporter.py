"""Performance reporter utility for generating performance reports."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """Utility class for collecting and reporting performance metrics."""

    def __init__(self, report_path: str = "performance_report.json"):
        """Initialize PerformanceReporter."""
        self.report_path = Path(report_path)
        self.measurements: list[dict] = []

    def add_measurement(
        self,
        page_name: str,
        url: str,
        metrics: dict,
        threshold_ms: int,
        exceeded: bool = False
    ) -> None:
        """
        Add a performance measurement.

        Args:
            page_name: Name of the page measured
            url: URL of the page
            metrics: Performance metrics dictionary
            threshold_ms: The threshold in milliseconds
            exceeded: Whether threshold was exceeded
        """
        measurement = {
            "page_name": page_name,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "threshold_ms": threshold_ms,
            "exceeded_threshold": exceeded
        }
        self.measurements.append(measurement)

        if exceeded:
            load_time = metrics.get("load_time_ms", "N/A")
            logger.warning(
                f"Performance threshold exceeded for {page_name}: "
                f"{load_time}ms > {threshold_ms}ms"
            )
        else:
            logger.info(f"Performance OK for {page_name}")

    def check_threshold(self, metrics: dict, threshold_ms: int) -> bool:
        """
        Check if any metric exceeds the threshold.

        Returns:
            True if threshold exceeded, False otherwise, None if invalid measurement
        """
        load_time = metrics.get("load_time_ms")
        if load_time is None or load_time <= 0:
            logger.warning(f"Invalid load_time: {load_time}")
            return False
        return load_time > threshold_ms

    def generate_report(self) -> dict:
        """Generate the performance report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_measurements": len(self.measurements),
            "thresholds_exceeded": sum(
                1 for m in self.measurements if m["exceeded_threshold"]
            ),
            "measurements": self.measurements,
            "summary": self._generate_summary()
        }
        return report

    def _generate_summary(self) -> dict:
        """Generate summary statistics."""
        if not self.measurements:
            return {}

        load_times = [
            m["metrics"].get("load_time_ms")
            for m in self.measurements
            if m["metrics"].get("load_time_ms")
        ]

        if not load_times:
            return {}

        return {
            "avg_load_time_ms": sum(load_times) / len(load_times),
            "max_load_time_ms": max(load_times),
            "min_load_time_ms": min(load_times),
            "total_pages_measured": len(self.measurements)
        }

    def save_report(self, filepath: Optional[str] = None) -> str:
        """
        Save the report to a JSON file.

        Returns:
            Path to the saved report
        """
        path = Path(filepath) if filepath else self.report_path
        report = self.generate_report()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Performance report saved to: {path}")
        return str(path)

    def print_summary(self) -> None:
        """Print a summary to the console."""
        report = self.generate_report()
        print("\n" + "=" * 50)
        print("PERFORMANCE REPORT SUMMARY")
        print("=" * 50)
        print(f"Total measurements: {report['total_measurements']}")
        print(f"Thresholds exceeded: {report['thresholds_exceeded']}")

        if report.get("summary"):
            summary = report["summary"]
            print(f"Average load time: {summary.get('avg_load_time_ms', 'N/A'):.2f}ms")
            print(f"Max load time: {summary.get('max_load_time_ms', 'N/A')}ms")
            print(f"Min load time: {summary.get('min_load_time_ms', 'N/A')}ms")

        print("=" * 50 + "\n")
