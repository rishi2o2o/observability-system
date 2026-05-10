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

