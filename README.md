# Observability System

A simple observability pipeline that demonstrates the collector → queue → processor architecture pattern for log ingestion.

## Project Structure

```text
observability-system/
├── collector/       # Reads logs and sends to queue
├── log_queue/       # In-memory queue for buffering
├── processor/       # Consumes from queue and sends to server
├── api/             # HTTP log ingestion server
└── storage/         # Reserved for future storage backends
```

## Day 4: Queue-Based Architecture

### Overview

The system now uses an in-memory queue to decouple the collector from the processor. Both components run in the same process but operate independently through the queue:

1. **Collector** reads log files and enqueues structured logs
2. **Queue** buffers logs in memory (thread-safe)
3. **Processor** (background thread) dequeues logs and sends them to the HTTP server

Current flow:

```text
sample_logs.txt → collector → in-memory queue → processor (thread) → HTTP POST /log → server storage
```

The collector and processor share the same in-memory queue within a single process, with the processor running in a background thread.

### Architecture

```text
┌─────────────┐      enqueue      ┌─────────────┐      dequeue      ┌─────────────┐
│   Log       │  ───────────────> │  In-Memory  │  ───────────────> │     Log     │
│  Collector  │   individual logs │    Queue    │   batches of 10   │  Processor  │
└─────────────┘                   └─────────────┘                   └─────────────┘
      │                                  │                                  │
      │ Reads plain-text                 │ Thread-safe                      │ HTTP POST
      │ logs from file                   │ buffer                           │ to server
      ▼                                  ▼                                  ▼
┌─────────────┐                   ┌─────────────┐                   ┌─────────────┐
│sample_logs  │                   │  Buffered   │                   │   Log       │
│   .txt      │                   │    Logs     │                   │   Server    │
└─────────────┘                   └─────────────┘                   └─────────────┘
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
- Enqueues each structured log to the in-memory queue
- Reports success/failure for each log

Example structured log:

```json
{
  "timestamp": "2026-04-30T14:20:00.000000Z",
  "level": "INFO",
  "message": "user login success"
}
```

### 2. In-Memory Queue ([`log_queue/log_queue.py`](log_queue/log_queue.py))

The queue:

- Provides thread-safe buffering between collector and processor
- Supports individual and batch enqueue/dequeue operations
- Tracks statistics (total enqueued, dequeued, current size)
- Implements blocking dequeue with timeout
- Can be configured with a maximum size (unlimited by default)

Key features:

- **Thread-safe**: Uses locks and condition variables
- **Blocking operations**: Dequeue waits for items if queue is empty
- **Batch support**: Efficient batch operations for the processor
- **Statistics**: Tracks throughput and queue health

### 3. Log Processor ([`processor/log_processor.py`](processor/log_processor.py))

The processor:

- Runs continuously in a loop
- Dequeues logs in batches of 10
- Sends each batch to the HTTP server
- Handles errors and retries
- Tracks processing statistics

Processing behavior:

- Waits up to 1 second for the first log in a batch
- Collects up to 10 logs per batch
- Sends batch as HTTP POST to server
- Reports success/failure for each batch

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

The server runs at `http://localhost:8080`.

### 3. Start the Processor

```bash
python -m processor.log_processor
```

### 4. Run the Collector

```bash
python3 run_system.py collector/sample_logs.txt
```

Or with a custom server URL:

```bash
python3 run_system.py collector/sample_logs.txt http://localhost:8080/log
```

This starts the processor in a background thread, then runs the collector to enqueue logs.

### 4. Inspect Collected Logs

```bash
curl http://localhost:8080/logs
curl http://localhost:8080/logs/count
curl http://localhost:8080/health
```

## Testing

Run the integration script:

```bash
sh test_integration.sh
```

The script:

1. Starts the server
2. Runs the unified system (collector + processor)
3. Checks that 10 logs were stored
4. Prints all stored logs
5. Stops the server

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


