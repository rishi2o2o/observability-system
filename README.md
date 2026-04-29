# Observability System

A simple observability pipeline that reads plain-text logs, converts them into structured JSON, buffers them in batches of 10, and sends each batch to an HTTP log server.

## Project Structure

```text
observability-system/
├── collector/       # Reads logs, structures them, and sends batches
├── processor/       # Reserved for future processing stages
├── storage/         # Reserved for future storage backends
└── api/             # HTTP log ingestion server
```

## Day 3: Buffered Log Collection

### Overview

The collector no longer sends each log line immediately. It now buffers structured logs and sends them to the server in batches of 10.

Current flow:

```text
sample_logs.txt -> collector -> batch of 10 logs -> HTTP POST /log -> in-memory server storage
```

### Architecture

```text
┌─────────────┐      batched HTTP POST      ┌─────────────┐
│   Log       │  ─────────────────────────> │   Log       │
│  Collector  │   10 logs per request       │   Server    │
└─────────────┘                             └─────────────┘
     │                                            │
     │ Reads plain-text logs                      │ Stores received logs
     │                                            │ in memory
     ▼                                            ▼
┌─────────────┐                             ┌─────────────┐
│sample_logs  │                             │  In-Memory  │
│   .txt      │                             │   Storage   │
└─────────────┘                             └─────────────┘
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
- Buffers logs until it has 10 entries
- Sends the batch to the server as one HTTP request
- Sends any remaining logs as a final partial batch

Example batch payload:

```json
{
  "logs": [
    {
      "timestamp": "2026-04-29T06:18:02.440035Z",
      "level": "INFO",
      "message": "user login success"
    }
  ]
}
```

### 2. Log Server ([`api/log_server.py`](api/log_server.py))

The server:

- Accepts `POST /log`
- Expects a JSON object with a `logs` array
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
python3 api/log_server.py
```

The server runs at `http://localhost:8080`.

### 3. Run the Collector

```bash
python3 collector/log_collector.py collector/sample_logs.txt
```

Or use a custom endpoint:

```bash
python3 collector/log_collector.py collector/sample_logs.txt http://localhost:8080/log
```

### 4. Inspect Collected Logs

```bash
curl http://localhost:8080/logs
curl http://localhost:8080/logs/count
curl http://localhost:8080/health
```

## Example

### Input file

```text
[INFO] user login success
[ERROR] database connection failed
...
```

### Collector behavior

The collector groups logs like this before sending:

```json
{
  "logs": [
    {
      "timestamp": "2026-04-29T06:18:02.440035Z",
      "level": "INFO",
      "message": "user login success"
    },
    {
      "timestamp": "2026-04-29T06:18:02.440120Z",
      "level": "ERROR",
      "message": "database connection failed"
    }
  ]
}
```

### Server response

```json
{
  "status": "success",
  "message": "Batch received successfully",
  "logs_received": 10
}
```

## Testing

Run the integration script:

```bash
sh test_integration.sh
```

The script:

1. Starts the server
2. Runs the collector
3. Checks that 10 logs were stored
4. Prints all stored logs
5. Stops the server

## Questions & Answers

### 1. Why do systems batch logs?

Systems batch logs to improve efficiency and reliability.

- Fewer network calls: sending 10 logs in one request creates much less overhead than sending 10 separate requests
- Better throughput: the collector spends less time waiting on network round-trips
- Lower CPU and connection overhead: fewer HTTP requests means fewer headers, socket operations, and request-handling costs
- Smoother ingestion: batching reduces pressure on the receiver during bursts of activity
- Better foundation for buffering and retries: if the destination is temporarily slow, batches are easier to queue and resend

In real observability systems, batching is a common optimization because logs are usually high-volume and individually very small.

### 2. What happens if we send every log individually?

Sending every log separately usually works at small scale, but it becomes inefficient quickly.

- High network overhead: each log carries the full cost of an HTTP request
- More load on the server: the server must parse, validate, and respond to many more requests
- Lower throughput: time is wasted on repeated request setup instead of moving useful log data
- Greater chance of bottlenecks: under high log volume, the pipeline can fall behind
- Higher cost in distributed systems: more requests means more connection handling, more resource usage, and more contention

So individual sending is simple, but batching is much closer to how real ingestion systems are built when performance matters.
