"""Main CLI entry point for NETCONF/YANG Test System

Command-line interface for YANG validation, test generation, and test execution.
"""

import argparse
import sys
import os
import json
from typing import Optional, List

from ..core.yang_parser import YANGParser
from ..core.yang_static_validator import YANGStaticValidator
from ..core.test_point_generator import TestPointGenerator
from ..executor.test_executor import TestExecutor
from ..reports.report_generator import ReportGenerator
from ..reports.test_result import TestResult, TestStatus


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="NETCONF/YANG Test System - Validate, Generate Tests, and Execute",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate YANG syntax
  %(prog)s validate example.yang

  # Generate test points
  %(prog)s generate example.yang -o tests.json

  # Run tests against device
  %(prog)s run tests.json --host 192.168.1.1 --user admin

  # Generate HTML report
  %(prog)s report results.json -o report.html
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate YANG file syntax")
    validate_parser.add_argument("yang_file", help="Path to YANG file")
    validate_parser.add_argument("-p", "--path", action="append", dest="search_paths",
                                 help="Additional search paths for imports")
    validate_parser.add_argument("-o", "--output", help="Output file for validation results")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate test points from YANG")
    generate_parser.add_argument("yang_file", help="Path to YANG file")
    generate_parser.add_argument("-o", "--output", default="test_points.json",
                                 help="Output file for test points (default: test_points.json)")
    generate_parser.add_argument("-t", "--types", nargs="+",
                                 choices=["syntax", "import", "feature", "netconf", "restconf", "capability", "all"],
                                 default=["all"], help="Test types to generate")
    generate_parser.add_argument("-s", "--severity", choices=["critical", "high", "medium", "low"],
                                 help="Filter by severity")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run test points against device")
    run_parser.add_argument("test_file", help="JSON file containing test points")
    run_parser.add_argument("--host", required=True, help="Device hostname or IP")
    run_parser.add_argument("--port", type=int, default=830, help="NETCONF port (default: 830)")
    run_parser.add_argument("--user", required=True, help="Username")
    run_parser.add_argument("--password", help="Password (will prompt if not provided)")
    run_parser.add_argument("-o", "--output", default="results.json",
                             help="Output file for results (default: results.json)")
    run_parser.add_argument("--timeout", type=int, default=30, help="Connection timeout (default: 30)")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate test report")
    report_parser.add_argument("result_file", help="JSON file containing test results")
    report_parser.add_argument("-o", "--output", default="report.html",
                               help="Output file (default: report.html)")
    report_parser.add_argument("-f", "--format", choices=["html", "json", "csv"], default="html",
                               help="Report format (default: html)")

    # Device info command
    device_parser = subparsers.add_parser("device", help="Show device capabilities")
    device_parser.add_argument("--host", required=True, help="Device hostname or IP")
    device_parser.add_argument("--port", type=int, default=830, help="NETCONF port (default: 830)")
    device_parser.add_argument("--user", required=True, help="Username")
    device_parser.add_argument("--password", help="Password (will prompt if not provided)")

    return parser


def validate_command(args) -> int:
    """Execute validate command"""
    print(f"Validating YANG file: {args.yang_file}")

    if not os.path.exists(args.yang_file):
        print(f"Error: File not found: {args.yang_file}")
        return 1

    validator = YANGStaticValidator()

    # Validate syntax
    print("Checking syntax...")
    result = validator.validate_syntax(args.yang_file)

    if result.is_valid:
        print("✓ Syntax validation passed")
    else:
        print("✗ Syntax validation failed:")
        for error in result.errors:
            print(f"  - {error}")

    # Validate imports if search paths provided
    if args.search_paths:
        print("Validating imports...")
        import_result = validator.validate_imports(args.yang_file, args.search_paths)
        if import_result.is_valid:
            print("✓ Import validation passed")
        else:
            print("✗ Import validation failed:")
            for error in import_result.errors:
                print(f"  - {error}")

    # Save results if output specified
    if args.output:
        output_data = {
            "file": args.yang_file,
            "syntax_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Results saved to: {args.output}")

    return 0 if result.is_valid else 1


def generate_command(args) -> int:
    """Execute generate command"""
    print(f"Generating test points from: {args.yang_file}")

    if not os.path.exists(args.yang_file):
        print(f"Error: File not found: {args.yang_file}")
        return 1

    generator = TestPointGenerator(args.yang_file)
    test_points = generator.generate_all_test_points()

    if not test_points:
        print("No test points generated")
        return 1

    # Filter by type if specified
    if "all" not in args.types:
        filtered = []
        type_map = {
            "syntax": "syntax_validation",
            "import": "module_import",
            "feature": "feature_condition",
            "netconf": "get_config",
            "restconf": "restconf_get",
            "capability": "capability_negotiation",
        }
        for tp in test_points:
            for t in args.types:
                if t in type_map and tp.test_type.value == type_map[t]:
                    filtered.append(tp)
                    break
        test_points = filtered

    # Filter by severity if specified
    if args.severity:
        test_points = [tp for tp in test_points if tp.severity.value == args.severity]

    # Save to file
    output_data = [tp.to_dict() for tp in test_points]
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Generated {len(test_points)} test points")
    print(f"  Saved to: {args.output}")

    return 0


def run_command(args) -> int:
    """Execute run command"""
    print(f"Running tests from: {args.test_file}")

    if not os.path.exists(args.test_file):
        print(f"Error: File not found: {args.test_file}")
        return 1

    # Load test points
    with open(args.test_file, 'r') as f:
        test_points_data = json.load(f)

    if not test_points_data:
        print("No test points to run")
        return 1

    # Get password if not provided
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Password: ")

    # Create executor
    executor = TestExecutor(
        host=args.host,
        port=args.port,
        username=args.user,
        password=password,
        timeout=args.timeout
    )

    # Run tests
    print(f"Connecting to {args.host}:{args.port}...")
    try:
        results = executor.execute_test_points(test_points_data)
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    # Save results
    results_data = [r.to_dict() for r in results]
    with open(args.output, 'w') as f:
        json.dump(results_data, f, indent=2)

    # Print summary
    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

    print(f"\n✓ Tests completed")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Results saved to: {args.output}")

    return 0 if failed == 0 else 1


def report_command(args) -> int:
    """Execute report command"""
    print(f"Generating report from: {args.result_file}")

    if not os.path.exists(args.result_file):
        print(f"Error: File not found: {args.result_file}")
        return 1

    # Load results
    with open(args.result_file, 'r') as f:
        results_data = json.load(f)

    # Generate report
    generator = ReportGenerator()

    if args.format == "html":
        html = generator.generate_html_report(results_data)
        with open(args.output, 'w') as f:
            f.write(html)
        print(f"✓ HTML report saved to: {args.output}")

    elif args.format == "json":
        with open(args.output, 'w') as f:
            json.dump(results_data, f, indent=2)
        print(f"✓ JSON report saved to: {args.output}")

    elif args.format == "csv":
        csv = generator.generate_csv_report(results_data)
        with open(args.output, 'w') as f:
            f.write(csv)
        print(f"✓ CSV report saved to: {args.output}")

    return 0


def device_command(args) -> int:
    """Execute device command - show device capabilities"""
    print(f"Connecting to {args.host}:{args.port}...")

    # Get password if not provided
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Password: ")

    from ..netconf.client import NETCONFClient

    client = NETCONFClient(
        host=args.host,
        port=args.port,
        username=args.user,
        password=password
    )

    try:
        client.connect()
        capabilities = client.get_capabilities()

        print("\n=== Device Capabilities ===\n")
        print(f"Session ID: {capabilities.get('session_id')}")
        print("\nServer Capabilities:")
        for cap in capabilities.get('server_capabilities', []):
            print(f"  - {cap}")

        client.disconnect()
        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1

    # Execute command
    command_map = {
        "validate": validate_command,
        "generate": generate_command,
        "run": run_command,
        "report": report_command,
        "device": device_command,
    }

    command_func = command_map.get(parsed_args.command)
    if command_func:
        return command_func(parsed_args)
    else:
        print(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
