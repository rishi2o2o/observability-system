#!/usr/bin/env python3
"""
Redis-Based Log Queue
A shared queue for buffering logs between collector and processor using Redis
"""

import json
import redis
from typing import Optional, List, Dict, Any


class LogQueue:
    """
    Redis-based queue for log messages.
    
    This queue acts as a buffer between the collector and processor,
    allowing them to operate independently across different processes.
    """
    
    def __init__(self, redis_host: str, redis_port: int, 
                 redis_db: int, queue_key: str):
        """
        Initialize the Redis log queue.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            queue_key: Redis key name for the queue
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.queue_key = queue_key
    
    def enqueue(self, log_entry: Dict[str, Any]) -> bool:
        """
        Add a log entry to the queue.
        
        Args:
            log_entry: Dictionary containing structured log data
            
        Returns:
            True if successfully enqueued
        """
        try:
            self.redis_client.lpush(self.queue_key, json.dumps(log_entry))
            return True
        except Exception:
            return False
    
    def enqueue_batch(self, log_entries: List[Dict[str, Any]]) -> int:
        """
        Add multiple log entries to the queue.
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            Number of entries successfully enqueued
        """
        try:
            pipeline = self.redis_client.pipeline()
            for entry in log_entries:
                pipeline.lpush(self.queue_key, json.dumps(entry))
            pipeline.execute()
            return len(log_entries)
        except Exception:
            return 0
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Remove and return a log entry from the queue.
        
        Args:
            timeout: Maximum time to wait for an item (None = wait forever, 0 = non-blocking)
            
        Returns:
            Log entry dictionary, or None if timeout occurred
        """
        try:
            if timeout is None:
                # Block forever
                result = self.redis_client.brpop(self.queue_key)
            elif timeout == 0:
                # Non-blocking
                result = self.redis_client.rpop(self.queue_key)
                if result:
                    result = (self.queue_key, result)
            else:
                # Block with timeout
                result = self.redis_client.brpop(self.queue_key, timeout=int(timeout))
            
            if result:
                return json.loads(result[1])

            return None

        except Exception:
            return None
    
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
        
        # Wait for at least one item
        first_entry = self.dequeue(timeout=timeout)
        if not first_entry:
            return batch
        
        batch.append(first_entry)
        
        # Collect up to batch_size items (non-blocking for remaining items)
        while len(batch) < batch_size:
            entry = self.dequeue(timeout=0)
            if not entry:
                break
            batch.append(entry)
        
        return batch
    
    def size(self) -> int:
        """Return the current number of items in the queue."""
        try:
            return self.redis_client.llen(self.queue_key)
        except Exception:
            return 0
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self.size() == 0
    
    def clear(self):
        """Remove all items from the queue."""
        try:
            self.redis_client.delete(self.queue_key)
        except Exception:
            pass


class LogQueueSingleton:
    _log_queue_instance = None

    @classmethod
    def get_instance(cls):
        if cls._log_queue_instance is None:
            cls._log_queue_instance = LogQueue(
                redis_host="localhost", 
                redis_port=6379, 
                redis_db=0,
                queue_key="log_queue",
            )
        return cls._log_queue_instance



