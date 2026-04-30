#!/usr/bin/env python3
"""
Unified System Runner
Runs collector and processor together to share the in-memory queue
"""

import sys
import time
import signal
import threading
from collector.log_collector import parse_log_line
from processor.log_processor import LogProcessor
from log_queue.log_queue import get_queue


def run_collector(file_path):
    """
    Read logs from a file and enqueue them.
    
    Args:
        file_path: Path to the log file
    """
    queue = get_queue()
    
    try:
        with open(file_path, 'r') as file:
            print(f"Reading logs from: {file_path}")
            print(f"Sending logs to: in-memory queue")
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
            
            # Print queue stats
            stats = queue.stats()
            print(f"Queue size: {stats['current_size']}")
            print(f"Total enqueued: {stats['total_enqueued']}")
                    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python run_system.py <log_file_path> [server_url]")
        print("Example: python run_system.py collector/sample_logs.txt")
        print("Example: python run_system.py collector/sample_logs.txt http://localhost:8080/log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) == 3 else "http://localhost:8080/log"
    
    # Create and start the processor in a background thread
    processor = LogProcessor(server_url, batch_size=10)
    processor.start()
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        processor.stop()
        processor.print_stats()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Give processor a moment to start
    time.sleep(0.5)
    
    # Run the collector
    run_collector(log_file)
    
    # Wait a bit for processor to finish processing
    print("\nWaiting for processor to finish...")
    time.sleep(3)
    
    # Stop the processor
    processor.stop()
    processor.print_stats()


if __name__ == "__main__":
    main()


# Made with Bob