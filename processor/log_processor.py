#!/usr/bin/env python3
"""
Log Processor
Consumes logs from the queue and sends them to the log server.
"""

import sys
import time
import requests
from datetime import datetime
from config import Config
from log_queue.log_queue import LogQueueSingleton


class LogProcessor:
    """
    Processes logs from the queue and sends them to the log server.
    
    The processor runs in a continuous loop, pulling batches of logs
    from the queue and forwarding them to the HTTP log server.
    """
    
    def __init__(self, server_url: str, batch_size: int):
        """
        Initialize the log processor.
        
        Args:
            server_url: URL of the log server endpoint
            batch_size: Number of logs to process in each batch
        """
        self.server_url = server_url
        self.batch_size = batch_size
        self.queue = LogQueueSingleton.get_instance()
        self.running = False
        self.thread = None
        self.stats = {
            "batches_sent": 0,
            "logs_sent": 0,
            "logs_failed": 0,
            "errors": 0
        }
    
    def _timestamp(self):
        """Get formatted timestamp for logging."""
        return datetime.now().strftime('%H:%M:%S')
    
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
            print(f"[{self._timestamp()}] Failed to send batch: {e}", file=sys.stderr)
            return False
    
    def process_batch(self):
        """
        Process one batch of logs from the queue.
        
        Returns:
            Number of logs processed
        """
        batch = self.queue.dequeue_batch(self.batch_size, timeout=3.0)
        
        if not batch:
            return 0
        
        if self.send_batch(batch):
            self.stats["batches_sent"] += 1
            self.stats["logs_sent"] += len(batch)
            print(f"[{self._timestamp()}] ✓ Processed batch of {len(batch)} logs")
            return len(batch)

        else:
            self.stats["logs_failed"] += len(batch)
            self.stats["errors"] += 1
            print(f"[{self._timestamp()}] ✗ Failed to process batch of {len(batch)} logs")
            return 0
    
    def run(self):
        """
        Main processing loop.
        Continuously processes batches from the queue until stopped.
        """
        print(f"[{self._timestamp()}] Processor started")
        print(f"  Server URL: {self.server_url}")
        print(f"  Batch size: {self.batch_size}")
        print("-" * 60)
        
        self.running = True
        
        while self.running:
            try:
                self.process_batch()
            except Exception as e:
                print(f"[{self._timestamp()}] Error in processing loop: {e}", file=sys.stderr)
                self.stats["errors"] += 1
                time.sleep(1)
        
        print(f"[{self._timestamp()}] Processor stopped")
    

    def print_stats(self):
        """Print processor statistics."""
        queue_stats = self.queue.stats()
        
        print("\n" + "=" * 60)
        print("Processor Statistics")
        print("=" * 60)
        print(f"Batches sent:     {self.stats['batches_sent']}")
        print(f"Logs sent:        {self.stats['logs_sent']}")
        print(f"Logs failed:      {self.stats['logs_failed']}")
        print(f"Errors:           {self.stats['errors']}")

        print("\nQueue Statistics")
        print("-" * 60)
        print(f"Current size:     {queue_stats['current_size']}")
        print(f"Total enqueued:   {queue_stats['total_enqueued']}")
        print(f"Total dequeued:   {queue_stats['total_dequeued']}")
        print("=" * 60)


def main():
    """Main entry point for the log processor."""

    server_url = f"http://{Config.LOG_SERVER_HOST}:{Config.LOG_SERVER_PORT}/log"
    batch_size = Config.BATCH_SIZE
    processor = LogProcessor(server_url, batch_size)
    processor.run()


if __name__ == "__main__":
    main()


