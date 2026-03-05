"""Test Report Generator

Generate test reports in various formats (HTML, JSON, XML).
Based on RFC 6241 (NETCONF), RFC 7950 (YANG), and RFC 8040 (RESTCONF).
"""

import json
import html
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .test_result import TestSuiteResult, TestResult, TestStatus, CapabilityResult, ValidationResult


class ReportGenerator:
    """
    Generate test reports in various formats.
    
    Supports HTML, JSON, and XML report generation for test results.
    """
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(self, result: TestSuiteResult, 
                            filename: Optional[str] = None) -> str:
        """
        Generate JSON report.
        
        Args:
            result: Test suite result
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Finalize result if not already done
        if not result.end_time:
            result.finalize()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def generate_html_report(self, result: TestSuiteResult,
                            filename: Optional[str] = None) -> str:
        """
        Generate HTML report.
        
        Args:
            result: Test suite result
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        
        # Finalize result if not already done
        if not result.end_time:
            result.finalize()
        
        html_content = self._generate_html_content(result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def generate_xml_report(self, result: TestSuiteResult,
                           filename: Optional[str] = None) -> str:
        """
        Generate XML report.
        
        Args:
            result: Test suite result
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Path to generated report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.xml"
        
        filepath = self.output_dir / filename
        
        # Finalize result if not already done
        if not result.end_time:
            result.finalize()
        
        xml_content = self._generate_xml_content(result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return str(filepath)
    
    def generate_summary_report(self, results: List[TestSuiteResult]) -> Dict[str, Any]:
        """
        Generate summary report from multiple test suites.
        
        Args:
            results: List of test suite results
            
        Returns:
            Summary dictionary
        """
        total_tests = sum(r.total_tests for r in results)
        passed_tests = sum(r.passed_tests for r in results)
        failed_tests = sum(r.failed_tests for r in results)
        skipped_tests = sum(r.skipped_tests for r in results)
        error_tests = sum(r.error_tests for r in results)
        
        return {
            "total_suites": len(results),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "error_tests": error_tests,
            "overall_success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "generated_at": datetime.now().isoformat(),
            "suites": [r.to_dict() for r in results],
        }
    
    def _generate_html_content(self, result: TestSuiteResult) -> str:
        """Generate HTML report content"""
        status_colors = {
            TestStatus.PASSED: "#28a745",
            TestStatus.FAILED: "#dc3545",
            TestStatus.SKIPPED: "#ffc107",
            TestStatus.ERROR: "#6c757d",
            TestStatus.PENDING: "#17a2b8",
            TestStatus.RUNNING: "#007bff",
        }
        
        rows = []
        for r in result.results:
            status_color = status_colors.get(r.status, "#6c757d")
            status_text = r.status.value.upper()
            
            row = f"""
            <tr>
                <td>{html.escape(r.test_id)}</td>
                <td>{html.escape(r.test_name)}</td>
                <td style="color: {status_color}; font-weight: bold;">{status_text}</td>
                <td>{r.execution_time:.3f}s</td>
                <td>{html.escape(r.rfc_reference)}</td>
                <td>{html.escape(r.error_message[:100] if r.error_message else '-')}</td>
            </tr>
            """
            rows.append(row)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NETCONF/YANG Test Report - {html.escape(result.suite_name)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 24px;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 6px;
            text-align: center;
        }}
        .summary-card .number {{
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }}
        .summary-card .label {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 4px;
        }}
        .passed .number {{ color: #28a745; }}
        .failed .number {{ color: #dc3545; }}
        .skipped .number {{ color: #ffc107; }}
        .error .number {{ color: #6c757d; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .metadata {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 20px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NETCONF/YANG Test Report</h1>
        <h2>{html.escape(result.suite_name)}</h2>
        
        <div class="summary">
            <div class="summary-card">
                <div class="number">{result.total_tests}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="summary-card passed">
                <div class="number">{result.passed_tests}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="number">{result.failed_tests}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card skipped">
                <div class="number">{result.skipped_tests}</div>
                <div class="label">Skipped</div>
            </div>
            <div class="summary-card error">
                <div class="number">{result.error_tests}</div>
                <div class="label">Errors</div>
            </div>
        </div>
        
        <h3>Test Results</h3>
        <table>
            <thead>
                <tr>
                    <th>Test ID</th>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>RFC Reference</th>
                    <th>Error Message</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        
        <div class="metadata">
            <strong>YANG File:</strong> {html.escape(result.yang_file)}<br>
            <strong>Start Time:</strong> {result.start_time}<br>
            <strong>End Time:</strong> {result.end_time}<br>
            <strong>Duration:</strong> {result.execution_duration:.2f}s<br>
            <strong>Success Rate:</strong> {result.success_rate:.1f}%
        </div>
    </div>
</body>
</html>
"""
        return html_template
    
    def _generate_xml_content(self, result: TestSuiteResult) -> str:
        """Generate XML report content"""
        tests_xml = []
        for r in result.results:
            test_xml = f"""        <test>
            <test_id>{html.escape(r.test_id)}</test_id>
            <test_name>{html.escape(r.test_name)}</test_name>
            <status>{r.status.value}</status>
            <passed>{str(r.passed).lower()}</passed>
            <actual_result><![CDATA[{r.actual_result}]]></actual_result>
            <expected_result><![CDATA[{r.expected_result}]]></expected_result>
            <error_message><![CDATA[{r.error_message}]]></error_message>
            <execution_time>{r.execution_time}</execution_time>
            <rfc_reference>{html.escape(r.rfc_reference)}</rfc_reference>
            <timestamp>{r.timestamp}</timestamp>
        </test>"""
            tests_xml.append(test_xml)
        
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<test_suite>
    <suite_name>{html.escape(result.suite_name)}</suite_name>
    <summary>
        <total_tests>{result.total_tests}</total_tests>
        <passed_tests>{result.passed_tests}</passed_tests>
        <failed_tests>{result.failed_tests}</failed_tests>
        <skipped_tests>{result.skipped_tests}</skipped_tests>
        <error_tests>{result.error_tests}</error_tests>
        <success_rate>{result.success_rate}</success_rate>
    </summary>
    <execution_info>
        <yang_file>{html.escape(result.yang_file)}</yang_file>
        <start_time>{result.start_time}</start_time>
        <end_time>{result.end_time}</end_time>
        <execution_duration>{result.execution_duration}</execution_duration>
    </execution_info>
    <tests>
{''.join(tests_xml)}
    </tests>
</test_suite>
"""
        return xml_template


@dataclass
class ReportConfig:
    """Report generation configuration"""
    format: str = "html"  # html, json, xml
    include_raw_responses: bool = False
    include_metadata: bool = True
    theme: str = "default"


def generate_default_report(result: TestSuiteResult,
                           output_dir: str = "./reports",
                           formats: List[str] = None) -> Dict[str, str]:
    """
    Generate reports in multiple formats.
    
    Args:
        result: Test suite result
        output_dir: Output directory for reports
        formats: List of formats to generate (default: ['html', 'json'])
        
    Returns:
        Dictionary mapping format to report file path
    """
    if formats is None:
        formats = ['html', 'json']
    
    generator = ReportGenerator(output_dir)
    reports = {}
    
    if 'json' in formats:
        reports['json'] = generator.generate_json_report(result)
    if 'html' in formats:
        reports['html'] = generator.generate_html_report(result)
    if 'xml' in formats:
        reports['xml'] = generator.generate_xml_report(result)
    
    return reports
