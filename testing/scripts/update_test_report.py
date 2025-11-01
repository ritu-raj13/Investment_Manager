"""
Script to update TEST_REPORTS.md with new test run results
Usage: Run after pytest execution to append results to the report
"""
import re
import os
from datetime import datetime

# Get the testing root directory
TESTING_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(TESTING_ROOT, 'reports', 'test_run_raw.log')
REPORT_FILE = os.path.join(TESTING_ROOT, 'reports', 'TEST_REPORTS.md')

def parse_pytest_output(log_file=None):
    """Parse pytest output to extract test statistics"""
    if log_file is None:
        log_file = LOG_FILE
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract summary line (e.g., "11 failed, 55 passed, 112 warnings, 24 errors in 37.17s")
        summary_pattern = r'(\d+)\s+failed,\s+(\d+)\s+passed,\s+\d+\s+warnings,\s+(\d+)\s+errors\s+in\s+([\d.]+)s'
        match = re.search(summary_pattern, content)
        
        if match:
            failed = int(match.group(1))
            passed = int(match.group(2))
            errors = int(match.group(3))
            duration = float(match.group(4))
            total = passed + failed + errors
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'duration': duration,
                'pass_rate': pass_rate
            }
        
        # If no failures, try the success pattern
        success_pattern = r'(\d+)\s+passed,\s+\d+\s+warnings\s+in\s+([\d.]+)s'
        match = re.search(success_pattern, content)
        
        if match:
            passed = int(match.group(1))
            duration = float(match.group(2))
            
            return {
                'total': passed,
                'passed': passed,
                'failed': 0,
                'errors': 0,
                'duration': duration,
                'pass_rate': 100.0
            }
        
        return None
    
    except FileNotFoundError:
        print(f"Error: {log_file} not found")
        return None


def append_test_run_to_report(stats, notes=''):
    """Append new test run to TEST_REPORTS.md"""
    if not stats:
        print("No statistics to append")
        return
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Determine status emoji
    if stats['pass_rate'] >= 95:
        status = '✅ Passing'
    elif stats['pass_rate'] >= 80:
        status = '🟢 Good'
    elif stats['pass_rate'] >= 60:
        status = '🟡 In Progress'
    else:
        status = '🔴 Failing'
    
    # Create table row
    new_row = f"| {date_str} | {stats['total']} | {stats['passed']} | {stats['failed']} | {stats['errors']} | {stats['pass_rate']:.1f}% | {status} | {notes} |"
    
    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the test history table and append new row
        table_pattern = r'(\|\s*Date\s*\|.*?\n\|[-\s|]+\n)((?:\|.*?\n)*)'
        
        def replace_table(match):
            header = match.group(1)
            existing_rows = match.group(2)
            return header + new_row + '\n' + existing_rows
        
        updated_content = re.sub(table_pattern, replace_table, content, count=1)
        
        # Update latest test run section
        updated_content = re.sub(
            r'\*\*Date:\*\* [^\n]+',
            f'**Date:** {datetime.now().strftime("%B %d, %Y")}',
            updated_content,
            count=1
        )
        
        updated_content = re.sub(
            r'\*\*Status:\*\* [^\n]+',
            f'**Status:** {status}',
            updated_content,
            count=1
        )
        
        updated_content = re.sub(
            r'\*\*Pass Rate:\*\* [^\n]+',
            f'**Pass Rate:** {stats["pass_rate"]:.1f}% ({stats["passed"]}/{stats["total"]} tests)',
            updated_content,
            count=1
        )
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Updated TEST_REPORTS.md with {date_str} test run")
        print(f"   Pass Rate: {stats['pass_rate']:.1f}% ({stats['passed']}/{stats['total']})")
        print(f"   Duration: {stats['duration']:.2f}s")
        
    except FileNotFoundError:
        print(f"Error: {REPORT_FILE} not found")
    except Exception as e:
        print(f"Error updating report: {e}")


if __name__ == '__main__':
    print("Parsing test results...")
    stats = parse_pytest_output()
    
    if stats:
        print(f"\nTest Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Passed: {stats['passed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Pass Rate: {stats['pass_rate']:.1f}%")
        print(f"  Duration: {stats['duration']:.2f}s")
        
        print("\nUpdating TEST_REPORTS.md...")
        append_test_run_to_report(stats, notes='Automated test run')
    else:
        print("Failed to parse test results")

