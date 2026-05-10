#!/usr/bin/env python3
"""
Log Collector with Queue Transport
Reads logs from a file, converts them to structured JSON format,
and sends them to an in-memory queue for processing
"""

import re
import sys
from datetime import datetime, timezone
from config import Config
from log_queue.log_queue import LogQueueSingleton


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
    Read logs from a file, convert them to structured JSON format,
    and send them to the queue.

    Args:
        file_path: Path to the log file
    """
    queue = LogQueueSingleton.get_instance()
    
    try:
        with open(file_path, 'r') as file:
            print(f"Reading logs from: {file_path}")
            print(f"Sending logs to: redis log queue")
            print("-" * 60)

            success_count = 0
            failure_count = 0

            for line_number, line in enumerate(file, 1):
                structured_log = parse_log_line(line)

                if not structured_log:
                    continue

                # Enqueue the log
                if queue.enqueue(structured_log):
                    success_count += 1
                    print(f"✓ Enqueued log line {line_number}")
                else:
                    failure_count += 1
                    print(f"✗ Failed to enqueue log line {line_number} (queue full)")

            print("-" * 60)
            print(f"Summary: {success_count} logs enqueued, {failure_count} failed")
            print(f"Queue size: {queue.size()}")
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the log collector."""
    collect_logs(Config.LOG_FILE_PATH)


if __name__ == "__main__":
    main()



