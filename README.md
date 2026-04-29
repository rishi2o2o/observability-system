# Observability System

A comprehensive observability system for collecting, processing, storing, and querying logs and metrics.

## Project Structure

```
observability-system/
├── collector/       # Log collection components
├── processor/       # Log processing and transformation
├── storage/         # Data storage layer
└── api/            # Log server and query API
```

## Day 2: HTTP-Based Log Collection

### Overview
The log collector now sends structured logs via HTTP POST to a dedicated log server, implementing a separation of concerns between log collection and log storage/processing.

### Architecture

```
┌─────────────┐      HTTP POST       ┌─────────────┐
│   Log       │  ───────────────────> │   Log       │
│  Collector  │  http://localhost:8080│   Server    │
└─────────────┘                       └─────────────┘
     │                                      │
     │ Reads logs                           │ Stores logs
     │ from file                            │ in memory
     ▼                                      ▼
┌─────────────┐                       ┌─────────────┐
│sample_logs  │                       │  In-Memory  │
│   .txt      │                       │   Storage   │
└─────────────┘                       └─────────────┘
```

### Components

#### 1. Log Collector ([`collector/log_collector.py`](collector/log_collector.py))
- Reads logs from a file
- Converts plain text logs to structured JSON format
- Sends logs via HTTP POST to the log server
- Provides feedback on successful/failed transmissions

#### 2. Log Server ([`api/log_server.py`](api/log_server.py))
- Receives logs via HTTP POST endpoint
- Validates log structure
- Stores logs in memory
- Provides query endpoints for log retrieval

### Usage

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Start the Log Server
```bash
python3 api/log_server.py
```

The server will start on `http://localhost:8080` with the following endpoints:
- `POST /log` - Receive log entries
- `GET /logs` - Retrieve all logs
- `GET /logs/count` - Get log count
- `POST /logs/clear` - Clear all logs
- `GET /health` - Health check

#### Step 3: Run the Log Collector
In a separate terminal:
```bash
python3 collector/log_collector.py collector/sample_logs.txt
```

Or specify a custom server URL:
```bash
python3 collector/log_collector.py collector/sample_logs.txt http://localhost:8080/log
```

#### Step 4: Query Logs
```bash
# Get all logs
curl http://localhost:8080/logs

# Get log count
curl http://localhost:8080/logs/count

# Check server health
curl http://localhost:8080/health
```

### Example

**Input (plain text log):**
```
[INFO] user login success
```

**Collector sends via HTTP POST:**
```json
{
  "timestamp": "2026-04-29T06:18:02.440035Z",
  "level": "INFO",
  "message": "user login success"
}
```

**Server response:**
```json
{
  "status": "success",
  "message": "Log received successfully"
}
```

### Testing

Run the integration test to verify the complete flow:
```bash
sh test_integration.sh
```

This will:
1. Start the log server
2. Send all sample logs via the collector
3. Verify logs were received
4. Display all collected logs
5. Clean up

## Questions & Answers

### 1. Why do observability systems separate collectors from storage?

Observability systems separate collectors from storage for several critical architectural reasons:

**Scalability & Performance:**
- **Independent Scaling**: Collectors and storage can scale independently based on their specific bottlenecks. You might need 100 collectors but only 10 storage nodes
- **Load Distribution**: Multiple collectors can send to the same storage, distributing the ingestion load
- **Resource Optimization**: Collectors are lightweight and can run on application servers, while storage requires more resources (disk, memory)

**Reliability & Fault Tolerance:**
- **Failure Isolation**: If storage goes down, collectors can buffer logs or send to backup storage without affecting the application
- **No Single Point of Failure**: Multiple storage backends can be used simultaneously
- **Graceful Degradation**: System continues collecting logs even if storage is temporarily unavailable

**Flexibility & Maintainability:**
- **Technology Independence**: Can swap storage backends (e.g., from files to Elasticsearch) without changing collectors
- **Multiple Destinations**: Same collector can send logs to multiple storage systems (e.g., local files + remote database)
- **Easier Updates**: Can update storage layer without touching deployed collectors

**Security & Compliance:**
- **Network Segmentation**: Collectors in DMZ can send to storage in secure internal network
- **Access Control**: Storage can have strict access controls while collectors have minimal permissions
- **Data Transformation**: Logs can be sanitized/filtered before reaching storage

**Operational Benefits:**
- **Centralized Management**: One storage system for logs from many sources
- **Easier Debugging**: Can test collectors and storage independently
- **Cost Efficiency**: Collectors are cheap to deploy; expensive storage is centralized

### 2. What problem does this architecture solve?

This HTTP-based collector-to-storage architecture solves several fundamental problems:

**1. Tight Coupling Problem:**
- **Before**: Collector directly writes to files/database, creating tight coupling
- **After**: HTTP interface provides loose coupling - collector doesn't need to know storage implementation details
- **Benefit**: Can change storage technology without modifying collector code

**2. Distributed System Challenges:**
- **Problem**: In microservices, each service generates logs on different machines
- **Solution**: All collectors send to centralized log server via HTTP
- **Benefit**: Single source of truth for all logs, easier correlation and analysis

**3. Resource Contention:**
- **Problem**: Writing logs directly to disk/database can slow down application
- **Solution**: Collector sends logs asynchronously via HTTP and continues
- **Benefit**: Application performance is not impacted by log storage speed

**4. Log Aggregation:**
- **Problem**: Logs scattered across multiple files/machines are hard to search
- **Solution**: Centralized log server receives all logs in one place
- **Benefit**: Easy to search, filter, and analyze logs from all sources

**5. Standardization:**
- **Problem**: Different applications might log in different formats
- **Solution**: HTTP API enforces a standard JSON schema for all logs
- **Benefit**: Consistent log format enables better tooling and automation

**6. Monitoring & Observability:**
- **Problem**: Hard to know if logs are being generated/stored correctly
- **Solution**: HTTP responses provide immediate feedback on success/failure
- **Benefit**: Can monitor log pipeline health in real-time

**7. Network Flexibility:**
- **Problem**: Direct file/database access requires complex network setup
- **Solution**: HTTP works over standard networks, through firewalls, load balancers
- **Benefit**: Easy to deploy in cloud, containers, or across data centers

**Real-World Example:**
```
Without separation:
App → Writes to local file → Manual collection → Hard to search

With separation:
App → Collector → HTTP → Log Server → Centralized storage → Easy querying
                                    ↓
                              Elasticsearch/Splunk/etc.
```

This architecture is the foundation for modern observability platforms like:
- **ELK Stack**: Logstash (collector) → Elasticsearch (storage)
- **Datadog**: Agent (collector) → Datadog API (storage)
- **Splunk**: Forwarder (collector) → Splunk Indexer (storage)



