#!/usr/bin/env python3
"""
Log Collector with HTTP Transport
Reads logs from a file, converts them to structured JSON format,
and sends them to a log server via HTTP POST
"""

import json
import re
import sys
import requests
from datetime import datetime, timezone


def parse_log_line(line):
    """
    Parse a log line and extract structured information.
    
    Expected format: [LEVEL] message
    Example: [INFO] user login success
    
    Returns a dictionary with structured log data.
    """
    line = line.strip()
    
    if not line:
        return None
    
    # Pattern to match [LEVEL] message format
    pattern = r'^\[(\w+)\]\s+(.+)$'
    match = re.match(pattern, line)
    
    if match:
        level = match.group(1)
        message = match.group(2)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level,
            "message": message
        }
    else:
        # If the line doesn't match the expected format, treat it as a raw message
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": "UNKNOWN",
            "message": line
        }


def send_log(log_data, server_url):
    """
    Send a structured log to the log server via HTTP POST.
    
    Args:
        log_data: Dictionary containing structured log data
        server_url: URL of the log server endpoint
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            server_url,
            json=log_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send log: {e}", file=sys.stderr)
        return False


def collect_logs(file_path, server_url="http://localhost:8080/log"):
    """
    Read logs from a file, convert them to structured JSON format,
    and send them to a log server via HTTP POST.
    
    Args:
        file_path: Path to the log file
        server_url: URL of the log server endpoint (default: http://localhost:8080/log)
    """
    try:
        with open(file_path, 'r') as file:
            print(f"Reading logs from: {file_path}")
            print(f"Sending logs to: {server_url}")
            print("-" * 60)
            
            success_count = 0
            failure_count = 0
            
            for line_number, line in enumerate(file, 1):
                structured_log = parse_log_line(line)
                
                if structured_log:
                    if send_log(structured_log, server_url):
                        success_count += 1
                        print(f"✓ Sent log {line_number}: [{structured_log['level']}] {structured_log['message'][:50]}...")
                    else:
                        failure_count += 1
                        print(f"✗ Failed to send log {line_number}")
            
            print("-" * 60)
            print(f"Summary: {success_count} logs sent successfully, {failure_count} failed")
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the log collector."""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python log_collector.py <log_file_path> [server_url]")
        print("Example: python log_collector.py sample_logs.txt")
        print("Example: python log_collector.py sample_logs.txt http://localhost:8080/log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) == 3 else "http://localhost:8080/log"
    
    collect_logs(log_file, server_url)


if __name__ == "__main__":
    main()

# Made with Bob
