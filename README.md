# Observability System

A simple observability pipeline that demonstrates the collector → queue → processor architecture pattern for log ingestion.


## Project Structure

```text
observability-system/
├── collector/       # Reads logs and sends to queue
├── log_queue/       # Redis-based queue for buffering
├── processor/       # Consumes from queue and sends to server
├── api/             # HTTP log ingestion server
└── storage/         # Reserved for future storage backends
```


## Components

### 1. Log Collector ([`collector/log_collector.py`](collector/log_collector.py))

The collector:

- Reads log lines from a file
- Parses lines like `[INFO] user login success`
- Converts each line into structured JSON with:
  - `timestamp`
  - `level`
  - `message`
- Enqueues each structured log to the redis-based log queue
- Reports success/failure for each log


### 2. Redis-Based Log Queue ([`log_queue/log_queue.py`](log_queue/log_queue.py))

The queue:

- Uses Redis for persistent, distributed buffering between collector and processor
- Supports individual and batch enqueue/dequeue operations
- Implements blocking dequeue with timeout using Redis BRPOP
- Allows multiple processes to share the same queue
- Provides queue size tracking via Redis LLEN
- Uses a singleton pattern for shared queue access


### 3. Log Processor ([`processor/log_processor.py`](processor/log_processor.py))

The processor:

- Runs continuously in a loop
- Dequeues logs in batches of 10
- Sends each batch to the HTTP server
- Handles errors and retries
- Tracks processing statistics


### 4. Log Server ([`api/log_server.py`](api/log_server.py))

The server:

- Accepts `POST /log` with batches of logs
- Validates every log in the batch
- Stores all valid logs in memory
- Exposes endpoints to inspect stored logs

Available endpoints:

- `POST /log` - Receive one batch of logs
- `GET /logs` - Retrieve all stored logs
- `GET /logs/count` - Get the total number of stored logs
- `POST /logs/clear` - Clear all stored logs
- `GET /health` - Health check


## Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Log Server

```bash
python -m api.log_server
```

### 3. Start the Processor

```bash
python -m processor.log_processor
```

### 4. Run the Collector

```bash
python -m collector.log_collector
```

### 4. Inspect Collected Logs

```bash
curl http://localhost:8080/logs
curl http://localhost:8080/logs/count
curl http://localhost:8080/health
```

## Questions & Answers

### 1. Why not send logs directly to processing?

Sending logs directly from the collector to the processor (or server) creates tight coupling and several problems:

- **Blocking**: The collector must wait for each network request to complete before reading the next log
- **No buffering**: If the processor/server is slow or temporarily unavailable, the collector stops making progress
- **Backpressure**: A slow downstream component blocks the entire pipeline
- **No decoupling**: The collector and processor must run at the same speed
- **Failure propagation**: If the processor fails, the collector fails too

Direct sending works for simple cases but doesn't scale well or handle real-world conditions like network delays, processing spikes, or component failures.

### 2. What problem does the queue solve?

The queue solves multiple critical problems:

**Decoupling**
- The collector and processor can run independently
- They don't need to know about each other's implementation
- Each component can be developed, tested, and scaled separately

**Buffering**
- Logs are buffered when the processor is slower than the collector
- The collector can continue reading logs even if the processor is temporarily down
- Smooths out bursts of log activity

**Asynchronous processing**
- The collector doesn't wait for network requests
- The processor can batch logs efficiently
- Each component operates at its own optimal speed

**Resilience**
- If the processor crashes, logs remain in the queue
- The collector doesn't fail when downstream components have issues
- Provides a buffer during temporary outages or slowdowns

**Performance**
- The collector can read logs as fast as possible
- The processor can optimize batch sizes for network efficiency
- No blocking on I/O operations

**Flexibility**
- Easy to add multiple processors (fan-out pattern)
- Can implement priority queues or routing logic
- Foundation for more advanced patterns like dead-letter queues

In production systems, queues are essential for building reliable, scalable observability pipelines. They're the foundation for handling high-volume log ingestion while maintaining system stability.


