#!/usr/bin/env python3
"""
In-Memory Log Queue
A simple thread-safe queue for buffering logs between collector and processor
"""

import threading
from collections import deque
from typing import Optional, List, Dict, Any


class LogQueue:
    """
    Thread-safe in-memory queue for log messages.
    
    This queue acts as a buffer between the collector and processor,
    allowing them to operate independently and handle backpressure.
    """
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize the log queue.
        
        Args:
            max_size: Maximum number of items in queue (None for unlimited)
        """
        self._queue = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._max_size = max_size
        self._total_enqueued = 0
        self._total_dequeued = 0
    
    def enqueue(self, log_entry: Dict[str, Any]) -> bool:
        """
        Add a log entry to the queue.
        
        Args:
            log_entry: Dictionary containing structured log data
            
        Returns:
            True if successfully enqueued, False if queue is full
        """
        with self._lock:
            if self._max_size and len(self._queue) >= self._max_size:
                return False
            
            self._queue.append(log_entry)
            self._total_enqueued += 1
            self._not_empty.notify()
            return True
    
    def enqueue_batch(self, log_entries: List[Dict[str, Any]]) -> int:
        """
        Add multiple log entries to the queue.
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            Number of entries successfully enqueued
        """
        count = 0
        with self._lock:
            for entry in log_entries:
                if self._max_size and len(self._queue) >= self._max_size:
                    break
                self._queue.append(entry)
                count += 1
            
            self._total_enqueued += count
            if count > 0:
                self._not_empty.notify()
        
        return count
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Remove and return a log entry from the queue.
        
        Args:
            timeout: Maximum time to wait for an item (None = wait forever)
            
        Returns:
            Log entry dictionary, or None if timeout occurred
        """
        with self._not_empty:
            while len(self._queue) == 0:
                if not self._not_empty.wait(timeout):
                    return None
            
            entry = self._queue.popleft()
            self._total_dequeued += 1
            return entry
    
    def dequeue_batch(self, batch_size: int, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Remove and return multiple log entries from the queue.
        
        Args:
            batch_size: Maximum number of entries to dequeue
            timeout: Maximum time to wait for first item (None = wait forever)
            
        Returns:
            List of log entry dictionaries (may be empty if timeout)
        """
        batch = []
        
        with self._not_empty:
            # Wait for at least one item
            while len(self._queue) == 0:
                if not self._not_empty.wait(timeout):
                    return batch
            
            # Collect up to batch_size items
            while len(batch) < batch_size and len(self._queue) > 0:
                batch.append(self._queue.popleft())
            
            self._total_dequeued += len(batch)
        
        return batch
    
    def size(self) -> int:
        """Return the current number of items in the queue."""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """Check if the queue is full."""
        with self._lock:
            if self._max_size is None:
                return False
            return len(self._queue) >= self._max_size
    
    def clear(self):
        """Remove all items from the queue."""
        with self._lock:
            self._queue.clear()
    
    def stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue metrics
        """
        with self._lock:
            return {
                "current_size": len(self._queue),
                "max_size": self._max_size,
                "total_enqueued": self._total_enqueued,
                "total_dequeued": self._total_dequeued,
                "is_full": self._max_size and len(self._queue) >= self._max_size,
                "is_empty": len(self._queue) == 0
            }


# Global queue instance (singleton pattern for simplicity)
_global_queue = None


def get_queue(max_size: Optional[int] = None) -> LogQueue:
    """
    Get or create the global queue instance.
    
    Args:
        max_size: Maximum queue size (only used on first call)
        
    Returns:
        The global LogQueue instance
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = LogQueue(max_size)
    return _global_queue


def reset_queue():
    """Reset the global queue instance (useful for testing)."""
    global _global_queue
    _global_queue = None


# Made with Bob