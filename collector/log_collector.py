#!/usr/bin/env python3
"""
Simple Log Collector
Reads logs from a file and converts them to structured JSON format
"""

import json
import re
import sys
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


def collect_logs(file_path):
    """
    Read logs from a file and convert them to structured JSON format.
    
    Args:
        file_path: Path to the log file
    """
    try:
        with open(file_path, 'r') as file:
            print("Reading logs from:", file_path)
            print("-" * 60)
            
            for line_number, line in enumerate(file, 1):
                structured_log = parse_log_line(line)
                
                if structured_log:
                    # Print as formatted JSON
                    print(json.dumps(structured_log, indent=2))
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the log collector."""
    if len(sys.argv) != 2:
        print("Usage: python log_collector.py <log_file_path>")
        print("Example: python log_collector.py sample_logs.txt")
        sys.exit(1)
    
    log_file = sys.argv[1]
    collect_logs(log_file)


if __name__ == "__main__":
    main()

# Made with Bob
