"""Performance reporter utility for generating performance reports."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """Utility class for collecting and reporting performance metrics."""

    MAX_HISTORY_RUNS = 50  # Keep last 50 runs

    def __init__(self, report_dir: str = "reports/performance"):
        """Initialize PerformanceReporter."""
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.measurements: list[dict] = []
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            True if threshold exceeded, False otherwise
        """
        load_time = metrics.get("load_time_ms")
        if load_time is None or load_time <= 0:
            logger.warning(f"Invalid load_time: {load_time}")
            return False
        return load_time > threshold_ms

    def _generate_summary(self) -> dict:
        """Generate summary statistics for current run."""
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
            "total_pages_measured": len(self.measurements),
            "thresholds_exceeded": sum(
                1 for m in self.measurements if m["exceeded_threshold"]
            )
        }

    def _load_history(self) -> list[dict]:
        """Load all historical runs from individual files."""
        history = []

        for file_path in sorted(self.report_dir.glob("run_*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    history.append(data)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load {file_path}: {e}")

        return history

    def _cleanup_old_runs(self) -> None:
        """Remove old run files, keeping only the last MAX_HISTORY_RUNS."""
        files = sorted(self.report_dir.glob("run_*.json"))

        if len(files) > self.MAX_HISTORY_RUNS:
            files_to_delete = files[:-self.MAX_HISTORY_RUNS]
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old performance file: {file_path}")
                except IOError as e:
                    logger.warning(f"Could not delete {file_path}: {e}")

    def save_report(self, filepath: Optional[str] = None) -> str:
        """
        Save the current run to a separate file and update summary.

        Returns:
            Path to the saved report
        """
        # Save current run to individual file
        run_file = self.report_dir / f"run_{self.run_id}.json"
        current_run = {
            "run_id": self.run_id,
            "generated_at": datetime.now().isoformat(),
            "measurements": self.measurements,
            "summary": self._generate_summary()
        }

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(current_run, f, indent=2, ensure_ascii=False)

        # Cleanup old runs
        self._cleanup_old_runs()

        # Update summary file with aggregated stats
        self._update_summary_file()

        logger.info(f"Performance report saved to: {run_file}")
        return str(run_file)

    def _update_summary_file(self) -> None:
        """Update the summary file with aggregated statistics."""
        history = self._load_history()

        # Calculate overall statistics
        all_load_times = []
        total_exceeded = 0

        for run in history:
            for m in run.get("measurements", []):
                lt = m.get("metrics", {}).get("load_time_ms")
                if lt and lt > 0:
                    all_load_times.append(lt)
                if m.get("exceeded_threshold"):
                    total_exceeded += 1

        overall_stats = {}
        if all_load_times:
            overall_stats = {
                "total_runs": len(history),
                "total_measurements": len(all_load_times),
                "total_thresholds_exceeded": total_exceeded,
                "overall_avg_load_time_ms": sum(all_load_times) / len(all_load_times),
                "overall_max_load_time_ms": max(all_load_times),
                "overall_min_load_time_ms": min(all_load_times)
            }

        # Get last 5 runs summary for quick view
        recent_runs = []
        for run in history[-5:]:
            recent_runs.append({
                "run_id": run.get("run_id"),
                "generated_at": run.get("generated_at"),
                "summary": run.get("summary", {})
            })

        summary = {
            "last_updated": datetime.now().isoformat(),
            "overall_statistics": overall_stats,
            "recent_runs": recent_runs,
            "all_run_files": [f.name for f in sorted(self.report_dir.glob("run_*.json"))]
        }

        summary_file = self.report_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def print_summary(self) -> None:
        """Print a summary to the console."""
        summary = self._generate_summary()
        history = self._load_history()

        print("\n" + "=" * 50)
        print("PERFORMANCE REPORT SUMMARY")
        print("=" * 50)
        print(f"Run ID: {self.run_id}")
        print(f"Total measurements: {summary.get('total_pages_measured', 0)}")
        print(f"Thresholds exceeded: {summary.get('thresholds_exceeded', 0)}")

        if summary:
            print(f"Average load time: {summary.get('avg_load_time_ms', 0):.2f}ms")
            print(f"Max load time: {summary.get('max_load_time_ms', 0):.2f}ms")
            print(f"Min load time: {summary.get('min_load_time_ms', 0):.2f}ms")

        # Show history info
        total_runs = len(history) + 1  # +1 for current run
        print(f"\nHistory: {total_runs} runs stored")
        print(f"Location: {self.report_dir}/")
        print("=" * 50 + "\n")

    def get_trend(self, page_name: str) -> list[dict]:
        """
        Get performance trend for a specific page across all runs.

        Args:
            page_name: Name of the page to get trend for

        Returns:
            List of measurements for that page over time
        """
        history = self._load_history()
        trend = []

        for run in history:
            for m in run.get("measurements", []):
                if m.get("page_name") == page_name:
                    trend.append({
                        "run_id": run.get("run_id"),
                        "timestamp": m.get("timestamp"),
                        "load_time_ms": m.get("metrics", {}).get("load_time_ms"),
                        "exceeded": m.get("exceeded_threshold")
                    })
        return trend
