"""HTML Report Generator for test results."""
import json
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generate HTML reports for test results."""

    def __init__(self):
        self.steps = []
        self.start_time = datetime.now()

    def add_step(self, name: str, status: str, details: dict = None):
        """Add a test step to the report."""
        self.steps.append({
            "name": name,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> dict:
        """Get test summary statistics."""
        total = len(self.steps)
        passed = sum(1 for s in self.steps if s["status"] == "PASS")
        warned = sum(1 for s in self.steps if s["status"] == "WARN")
        failed = sum(1 for s in self.steps if s["status"] == "FAIL")

        return {
            "total": total,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "duration": str(datetime.now() - self.start_time)
        }

    def print_summary(self):
        """Print summary to console."""
        summary = self.get_summary()
        print(f"\nTotal Steps: {summary['total']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Warnings: {summary['warned']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Duration: {summary['duration']}")

    def save_html_report(self, filepath: Path) -> str:
        """Generate and save HTML report."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        summary = self.get_summary()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenLibrary Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #4CAF50;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            font-size: 2em;
            margin-bottom: 5px;
        }}
        .summary-card.passed h3 {{ color: #4CAF50; }}
        .summary-card.warned h3 {{ color: #FF9800; }}
        .summary-card.failed h3 {{ color: #f44336; }}
        .summary-card.total h3 {{ color: #2196F3; }}
        .steps {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .step {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .step:last-child {{ border-bottom: none; }}
        .step-status {{
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.85em;
            min-width: 70px;
            text-align: center;
        }}
        .step-status.PASS {{ background: #E8F5E9; color: #2E7D32; }}
        .step-status.WARN {{ background: #FFF3E0; color: #E65100; }}
        .step-status.FAIL {{ background: #FFEBEE; color: #C62828; }}
        .step-name {{
            font-weight: 500;
            flex: 1;
        }}
        .step-details {{
            font-size: 0.85em;
            color: #666;
        }}
        .details-toggle {{
            cursor: pointer;
            color: #2196F3;
            font-size: 0.85em;
        }}
        .details-content {{
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .screenshots {{
            margin-top: 30px;
        }}
        .screenshots h2 {{
            margin-bottom: 15px;
        }}
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .screenshot-card {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .screenshot-card img {{
            width: 100%;
            height: auto;
        }}
        .screenshot-card .caption {{
            padding: 10px;
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OpenLibrary Automation Test Report</h1>

        <div class="summary">
            <div class="summary-card total">
                <h3>{summary['total']}</h3>
                <p>Total Steps</p>
            </div>
            <div class="summary-card passed">
                <h3>{summary['passed']}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card warned">
                <h3>{summary['warned']}</h3>
                <p>Warnings</p>
            </div>
            <div class="summary-card failed">
                <h3>{summary['failed']}</h3>
                <p>Failed</p>
            </div>
        </div>

        <div class="steps">
            <h2 style="padding: 15px 20px; background: #f9f9f9; border-bottom: 1px solid #eee;">Test Steps</h2>
            {"".join(self._render_step(step, i) for i, step in enumerate(self.steps))}
        </div>

        <div class="footer">
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Duration: {summary['duration']}</p>
        </div>
    </div>

    <script>
        function toggleDetails(id) {{
            const el = document.getElementById(id);
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }}
    </script>
</body>
</html>
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return str(filepath)

    def _render_step(self, step: dict, index: int) -> str:
        """Render a single step as HTML."""
        details_id = f"details-{index}"
        details_json = json.dumps(step["details"], indent=2, ensure_ascii=False)

        return f"""
            <div class="step">
                <span class="step-status {step['status']}">{step['status']}</span>
                <span class="step-name">{step['name']}</span>
                <span class="details-toggle" onclick="toggleDetails('{details_id}')">
                    [Details]
                </span>
            </div>
            <div id="{details_id}" class="details-content" style="margin: 0 20px 15px 20px;">
{details_json}
            </div>
        """

    def save_json_report(self, filepath: Path) -> str:
        """Save report as JSON."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "steps": self.steps
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return str(filepath)
