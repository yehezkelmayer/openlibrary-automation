"""HTML Report Generator for test results."""
import base64
import json
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generate HTML reports for test results."""

    def __init__(self, screenshots_dir: str = "screenshots"):
        self.steps = []
        self.start_time = datetime.now()
        self.screenshots_dir = Path(screenshots_dir)

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

    def _get_screenshots(self) -> list[dict]:
        """Get all screenshots with embedded base64 data."""
        screenshots = []
        if not self.screenshots_dir.exists():
            return screenshots

        for img_path in sorted(self.screenshots_dir.glob("*.png")):
            try:
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")

                # Parse filename for metadata
                name = img_path.stem
                parts = name.split("_")
                index = parts[0] if parts else "?"
                status = parts[-1] if len(parts) > 1 else "unknown"
                title = "_".join(parts[1:-1]) if len(parts) > 2 else name

                screenshots.append({
                    "name": name,
                    "title": title.replace("_", " ").title(),
                    "index": index,
                    "status": status.upper(),
                    "data": img_data
                })
            except Exception:
                continue

        return screenshots

    def _render_details(self, step: dict) -> str:
        """Render step details in a user-friendly format."""
        details = step.get("details", {})
        name = step.get("name", "")

        # Clear Reading Lists
        if "removed" in details:
            removed = details.get("removed", {})
            total = details.get("total_removed", 0)
            items = "".join(
                f'<div class="detail-item"><span class="label">{k}:</span> <span class="value">{v} removed</span></div>'
                for k, v in removed.items()
            )
            return f'''
                <div class="detail-card">
                    <div class="detail-header">Cleared {total} books total</div>
                    {items}
                </div>
            '''

        # Search Books
        if "searches" in details:
            searches = details.get("searches", [])
            urls = details.get("urls", [])
            search_items = "".join(
                f'<div class="search-item"><span class="query">"{s["query"]}"</span> before {s["max_year"]} (limit: {s["limit"]})</div>'
                for s in searches
            )
            url_items = "".join(
                f'<div class="url-item"><a href="{url}" target="_blank">{url.split("/")[-1]}</a></div>'
                for url in urls
            )
            return f'''
                <div class="detail-card">
                    <div class="detail-header">Search Queries</div>
                    {search_items}
                    <div class="detail-header" style="margin-top: 15px;">Found {len(urls)} Books</div>
                    <div class="url-list">{url_items}</div>
                </div>
            '''

        # Add to Reading List
        if "attempted" in details and "actually_added" in details:
            attempted = details.get("attempted", 0)
            added = details.get("actually_added", 0)
            success_rate = (added / attempted * 100) if attempted > 0 else 0
            return f'''
                <div class="detail-card">
                    <div class="stat-grid">
                        <div class="stat-item">
                            <span class="stat-value">{attempted}</span>
                            <span class="stat-label">Attempted</span>
                        </div>
                        <div class="stat-item success">
                            <span class="stat-value">{added}</span>
                            <span class="stat-label">Added</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-value">{success_rate:.0f}%</span>
                            <span class="stat-label">Success Rate</span>
                        </div>
                    </div>
                </div>
            '''

        # Verify Reading List
        if "expected" in details and "actual" in details:
            expected = details.get("expected", 0)
            actual = details.get("actual", 0)
            match = expected == actual
            return f'''
                <div class="detail-card">
                    <div class="stat-grid">
                        <div class="stat-item">
                            <span class="stat-value">{expected}</span>
                            <span class="stat-label">Expected</span>
                        </div>
                        <div class="stat-item {'success' if match else 'error'}">
                            <span class="stat-value">{actual}</span>
                            <span class="stat-label">Actual</span>
                        </div>
                        <div class="stat-item {'success' if match else 'error'}">
                            <span class="stat-value">{'✓' if match else '✗'}</span>
                            <span class="stat-label">Match</span>
                        </div>
                    </div>
                </div>
            '''

        # Performance metrics
        if "load_time_ms" in details:
            load_time = details.get("load_time_ms", 0)
            dom_time = details.get("dom_content_loaded_ms", 0)
            paint_time = details.get("first_paint_ms", 0)
            threshold = details.get("threshold_ms", 0)
            exceeded = details.get("exceeded", False)

            # Calculate percentage for progress bar
            pct = min((load_time / threshold * 100), 150) if threshold > 0 else 0
            bar_color = "#f44336" if exceeded else "#4CAF50"

            return f'''
                <div class="detail-card">
                    <div class="perf-metric">
                        <div class="perf-header">
                            <span>Load Time</span>
                            <span class="{'exceeded' if exceeded else 'ok'}">{load_time:.0f}ms / {threshold}ms</span>
                        </div>
                        <div class="perf-bar">
                            <div class="perf-fill" style="width: {min(pct, 100)}%; background: {bar_color};"></div>
                            <div class="perf-threshold" style="left: {100 / 1.5}%;"></div>
                        </div>
                    </div>
                    <div class="perf-details">
                        <div class="perf-item">
                            <span class="label">DOM Content Loaded:</span>
                            <span class="value">{dom_time:.0f}ms</span>
                        </div>
                        <div class="perf-item">
                            <span class="label">First Paint:</span>
                            <span class="value">{paint_time:.0f}ms</span>
                        </div>
                    </div>
                </div>
            '''

        # Default: JSON display
        if details:
            return f'''
                <div class="detail-card">
                    <pre class="json-display">{json.dumps(details, indent=2, ensure_ascii=False)}</pre>
                </div>
            '''

        return '<div class="detail-card"><p class="no-details">No details available</p></div>'

    def save_html_report(self, filepath: Path) -> str:
        """Generate and save HTML report."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        summary = self.get_summary()
        screenshots = self._get_screenshots()

        # Generate steps HTML
        steps_html = ""
        for i, step in enumerate(self.steps):
            details_id = f"details-{i}"
            details_html = self._render_details(step)

            steps_html += f'''
                <div class="step-card">
                    <div class="step-header" onclick="toggleDetails('{details_id}')">
                        <span class="step-status {step['status']}">{step['status']}</span>
                        <span class="step-name">{step['name']}</span>
                        <span class="step-toggle">▼</span>
                    </div>
                    <div id="{details_id}" class="step-details">
                        {details_html}
                    </div>
                </div>
            '''

        # Generate screenshots HTML
        screenshots_html = ""
        if screenshots:
            screenshot_cards = ""
            for ss in screenshots:
                status_class = "success" if ss["status"] in ["WANT_TO_READ", "ALREADY_READ"] else ""
                screenshot_cards += f'''
                    <div class="screenshot-card">
                        <div class="screenshot-img" onclick="openModal(this)">
                            <img src="data:image/png;base64,{ss['data']}" alt="{ss['title']}" loading="lazy">
                        </div>
                        <div class="screenshot-caption">
                            <span class="screenshot-index">#{ss['index']}</span>
                            <span class="screenshot-title">{ss['title']}</span>
                            <span class="screenshot-status {status_class}">{ss['status'].replace('_', ' ')}</span>
                        </div>
                    </div>
                '''

            screenshots_html = f'''
                <section class="section screenshots-section">
                    <h2>Screenshots ({len(screenshots)})</h2>
                    <div class="screenshot-grid">
                        {screenshot_cards}
                    </div>
                </section>
            '''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenLibrary Test Report</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --error: #dc2626;
            --bg: #f8fafc;
            --card: #ffffff;
            --border: #e2e8f0;
            --text: #1e293b;
            --text-muted: #64748b;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 24px;
        }}

        .header h1 {{
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .header-meta {{
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            opacity: 0.9;
        }}

        /* Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .summary-card {{
            background: var(--card);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }}

        .summary-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            line-height: 1;
        }}

        .summary-card .label {{
            font-size: 0.85em;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        .summary-card.total .number {{ color: var(--primary); }}
        .summary-card.passed .number {{ color: var(--success); }}
        .summary-card.warned .number {{ color: var(--warning); }}
        .summary-card.failed .number {{ color: var(--error); }}

        /* Sections */
        .section {{
            background: var(--card);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }}

        .section h2 {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border);
        }}

        /* Step Cards */
        .step-card {{
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }}

        .step-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            cursor: pointer;
            background: #fafafa;
            transition: background 0.2s;
        }}

        .step-header:hover {{
            background: #f1f5f9;
        }}

        .step-status {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .step-status.PASS {{ background: #dcfce7; color: #166534; }}
        .step-status.WARN {{ background: #fef3c7; color: #92400e; }}
        .step-status.FAIL {{ background: #fee2e2; color: #991b1b; }}

        .step-name {{
            flex: 1;
            font-weight: 500;
        }}

        .step-toggle {{
            color: var(--text-muted);
            transition: transform 0.2s;
        }}

        .step-details {{
            display: none;
            padding: 16px;
            background: white;
            border-top: 1px solid var(--border);
        }}

        .step-details.open {{
            display: block;
        }}

        /* Detail Cards */
        .detail-card {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 16px;
        }}

        .detail-header {{
            font-weight: 600;
            font-size: 0.9em;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}

        .detail-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid var(--border);
        }}

        .detail-item:last-child {{ border-bottom: none; }}

        .detail-item .label {{ color: var(--text-muted); }}
        .detail-item .value {{ font-weight: 500; }}

        /* Search items */
        .search-item {{
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}

        .search-item .query {{
            color: var(--primary);
            font-weight: 500;
        }}

        .url-list {{
            max-height: 200px;
            overflow-y: auto;
        }}

        .url-item {{
            padding: 6px 0;
            font-size: 0.9em;
        }}

        .url-item a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .url-item a:hover {{
            text-decoration: underline;
        }}

        /* Stat Grid */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            text-align: center;
        }}

        .stat-item {{
            padding: 12px;
            background: white;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}

        .stat-item.success {{ border-color: var(--success); background: #f0fdf4; }}
        .stat-item.error {{ border-color: var(--error); background: #fef2f2; }}

        .stat-value {{
            display: block;
            font-size: 1.8em;
            font-weight: 700;
            color: var(--text);
        }}

        .stat-item.success .stat-value {{ color: var(--success); }}
        .stat-item.error .stat-value {{ color: var(--error); }}

        .stat-label {{
            font-size: 0.8em;
            color: var(--text-muted);
        }}

        /* Performance Metrics */
        .perf-metric {{
            margin-bottom: 16px;
        }}

        .perf-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9em;
        }}

        .perf-header .exceeded {{ color: var(--error); font-weight: 600; }}
        .perf-header .ok {{ color: var(--success); font-weight: 600; }}

        .perf-bar {{
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }}

        .perf-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}

        .perf-threshold {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #1e293b;
        }}

        .perf-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }}

        .perf-item {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }}

        .perf-item .label {{ color: var(--text-muted); }}

        /* JSON Display */
        .json-display {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            overflow-x: auto;
        }}

        .no-details {{
            color: var(--text-muted);
            font-style: italic;
        }}

        /* Screenshots */
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}

        .screenshot-card {{
            background: #fafafa;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .screenshot-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .screenshot-img {{
            cursor: pointer;
            aspect-ratio: 16/10;
            overflow: hidden;
        }}

        .screenshot-img img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.2s;
        }}

        .screenshot-img:hover img {{
            transform: scale(1.05);
        }}

        .screenshot-caption {{
            padding: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            background: white;
        }}

        .screenshot-index {{
            background: var(--primary);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }}

        .screenshot-title {{
            flex: 1;
            font-size: 0.9em;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .screenshot-status {{
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 4px;
            background: #e2e8f0;
            color: var(--text-muted);
        }}

        .screenshot-status.success {{
            background: #dcfce7;
            color: #166534;
        }}

        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .modal.open {{
            display: flex;
        }}

        .modal img {{
            max-width: 100%;
            max-height: 90vh;
            border-radius: 8px;
        }}

        .modal-close {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 1.5em;
            cursor: pointer;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85em;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>OpenLibrary Automation Test Report</h1>
            <div class="header-meta">
                <span>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span>Duration: {summary['duration']}</span>
            </div>
        </header>

        <div class="summary-grid">
            <div class="summary-card total">
                <div class="number">{summary['total']}</div>
                <div class="label">Total Steps</div>
            </div>
            <div class="summary-card passed">
                <div class="number">{summary['passed']}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card warned">
                <div class="number">{summary['warned']}</div>
                <div class="label">Warnings</div>
            </div>
            <div class="summary-card failed">
                <div class="number">{summary['failed']}</div>
                <div class="label">Failed</div>
            </div>
        </div>

        <section class="section">
            <h2>Test Steps</h2>
            {steps_html}
        </section>

        {screenshots_html}

        <footer class="footer">
            OpenLibrary Automation Test Suite
        </footer>
    </div>

    <div class="modal" id="imageModal" onclick="closeModal()">
        <button class="modal-close" onclick="closeModal()">&times;</button>
        <img id="modalImage" src="" alt="Screenshot">
    </div>

    <script>
        function toggleDetails(id) {{
            const el = document.getElementById(id);
            const toggle = el.previousElementSibling.querySelector('.step-toggle');
            el.classList.toggle('open');
            toggle.style.transform = el.classList.contains('open') ? 'rotate(180deg)' : '';
        }}

        function openModal(el) {{
            const img = el.querySelector('img');
            document.getElementById('modalImage').src = img.src;
            document.getElementById('imageModal').classList.add('open');
        }}

        function closeModal() {{
            document.getElementById('imageModal').classList.remove('open');
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});
    </script>
</body>
</html>'''

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return str(filepath)

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
