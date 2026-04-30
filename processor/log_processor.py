#!/usr/bin/env python3
"""
Log Processor
Consumes logs from the queue and sends them to the log server
"""

import sys
import time
import signal
import requests
import threading
from typing import Optional
from datetime import datetime
from log_queue.log_queue import get_queue


class LogProcessor:
    """
    Processes logs from the queue and sends them to the log server.
    
    The processor runs in a continuous loop, pulling batches of logs
    from the queue and forwarding them to the HTTP log server.
    """
    
    def __init__(self, server_url: str = "http://localhost:8080/log", batch_size: int = 10):
        """
        Initialize the log processor.
        
        Args:
            server_url: URL of the log server endpoint
            batch_size: Number of logs to process in each batch
        """
        self.server_url = server_url
        self.batch_size = batch_size
        self.queue = get_queue()
        self.running = False
        self.thread = None
        self.stats = {
            "batches_sent": 0,
            "logs_sent": 0,
            "logs_failed": 0,
            "errors": 0
        }
        self._stats_lock = threading.Lock()
    
    def send_batch(self, log_batch):
        """
        Send a batch of logs to the log server via HTTP POST.
        
        Args:
            log_batch: List of log entry dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                self.server_url,
                json={"logs": log_batch},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to send batch: {e}", file=sys.stderr)
            return False
    
    def process_batch(self):
        """
        Process one batch of logs from the queue.
        
        Returns:
            Number of logs processed
        """
        # Dequeue a batch (wait up to 1 second for first item)
        batch = self.queue.dequeue_batch(self.batch_size, timeout=1.0)
        
        if not batch:
            return 0
        
        # Send the batch to the server
        if self.send_batch(batch):
            with self._stats_lock:
                self.stats["batches_sent"] += 1
                self.stats["logs_sent"] += len(batch)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Processed batch of {len(batch)} logs")
            return len(batch)
        else:
            with self._stats_lock:
                self.stats["logs_failed"] += len(batch)
                self.stats["errors"] += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Failed to process batch of {len(batch)} logs")
            return 0
    
    def run(self):
        """
        Main processing loop.
        Continuously processes batches from the queue until stopped.
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processor started")
        print(f"  Server URL: {self.server_url}")
        print(f"  Batch size: {self.batch_size}")
        print("-" * 60)
        
        self.running = True
        
        while self.running:
            try:
                self.process_batch()
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in processing loop: {e}", file=sys.stderr)
                with self._stats_lock:
                    self.stats["errors"] += 1
                time.sleep(1)  # Brief pause on error
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processor stopped")
    
    def start(self):
        """Start the processor in a background thread."""
        if self.running:
            print("Processor is already running")
            return
        
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the processor gracefully."""
        if not self.running:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopping processor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
    
    def get_stats(self):
        """Get processor statistics."""
        with self._stats_lock:
            return self.stats.copy()
    
    def print_stats(self):
        """Print processor statistics."""
        stats = self.get_stats()
        queue_stats = self.queue.stats()
        
        print("\n" + "=" * 60)
        print("Processor Statistics")
        print("=" * 60)
        print(f"Batches sent:     {stats['batches_sent']}")
        print(f"Logs sent:        {stats['logs_sent']}")
        print(f"Logs failed:      {stats['logs_failed']}")
        print(f"Errors:           {stats['errors']}")
        print("\nQueue Statistics")
        print("-" * 60)
        print(f"Current size:     {queue_stats['current_size']}")
        print(f"Total enqueued:   {queue_stats['total_enqueued']}")
        print(f"Total dequeued:   {queue_stats['total_dequeued']}")
        print("=" * 60)


def main():
    """Main entry point for the log processor."""
    if len(sys.argv) < 1 or len(sys.argv) > 3:
        print("Usage: python log_processor.py [server_url] [batch_size]")
        print("Example: python log_processor.py")
        print("Example: python log_processor.py http://localhost:8080/log 10")
        sys.exit(1)
    
    server_url = sys.argv[1] if len(sys.argv) >= 2 else "http://localhost:8080/log"
    batch_size = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
    
    processor = LogProcessor(server_url, batch_size)
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        processor.stop()
        processor.print_stats()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the processor
    try:
        processor.run()
    except KeyboardInterrupt:
        processor.stop()
        processor.print_stats()


if __name__ == "__main__":
    main()


# Made with Bob