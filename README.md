# Observability System

A comprehensive observability system for collecting, processing, storing, and querying logs and metrics.

## Project Structure

```
observability-system/
├── collector/       # Log collection components
├── processor/       # Log processing and transformation
├── storage/         # Data storage layer
└── api/            # Query and retrieval API
```

## Day 1: Log Collector

### Overview
A simple log collector that reads logs from a file and converts them to structured JSON format.

### Usage

```bash
cd collector
python3 log_collector.py sample_logs.txt
```

### Example

**Input (plain text log):**
```
[INFO] user login success
```

**Output (structured JSON):**
```json
{
  "timestamp": "2026-04-29T05:35:40.039540Z",
  "level": "INFO",
  "message": "user login success"
}
```

## Questions & Answers

### 1. Why is structured logging useful?

Structured logging is useful for several critical reasons:

- **Machine Readability**: JSON format allows automated parsing and processing by log aggregation tools, monitoring systems, and analytics platforms without complex regex patterns
- **Consistent Schema**: Every log entry follows the same structure (timestamp, level, message), making it predictable and easier to work with
- **Queryability**: Structured logs can be easily filtered, searched, and aggregated. For example, you can quickly find all ERROR-level logs or count occurrences by log level
- **Integration**: Modern observability tools (Elasticsearch, Splunk, Datadog, etc.) are built to ingest and index structured data efficiently
- **Metadata Enrichment**: Easy to add additional fields like `user_id`, `request_id`, `service_name` without breaking existing parsers
- **Performance**: Parsing structured logs is faster than parsing unstructured text with regex patterns
- **Analytics**: Enables complex queries like "show me all ERROR logs from the authentication service in the last hour"

### 2. Why do observability systems avoid plain text logs?

Observability systems avoid plain text logs because:

- **Parsing Complexity**: Plain text requires custom regex patterns for each log format, which are brittle and error-prone. Different services may use different formats, making centralized logging difficult
- **Ambiguity**: Plain text can be ambiguous. For example, is "user: admin" a key-value pair or just part of a message? Structured formats eliminate this ambiguity
- **Performance at Scale**: When processing millions of logs per second, parsing plain text is computationally expensive. Structured formats can be parsed much faster
- **Loss of Context**: Plain text often loses important metadata. In structured logs, you can include `trace_id`, `span_id`, `user_id`, etc., which are essential for distributed tracing
- **Difficult Aggregation**: Calculating metrics like "error rate per service" requires parsing and grouping plain text, which is slow and unreliable
- **No Type Safety**: Plain text doesn't preserve data types. Is "123" a string or a number? Structured formats maintain type information
- **Limited Tooling**: Modern observability platforms (Prometheus, Grafana, ELK stack) are designed for structured data and provide powerful visualization and alerting capabilities that don't work well with plain text
- **Correlation**: In microservices architectures, correlating logs across services requires consistent structured fields like `request_id` or `trace_id`, which are impossible to reliably extract from plain text

**Example of the problem:**
```
Plain text: "Error: Failed to connect to database at 10:30:45"
```
Questions that are hard to answer:
- Which database?
- Which service?
- What was the request ID?
- Was this part of a larger transaction?

**Structured version:**
```json
{
  "timestamp": "2026-04-29T10:30:45Z",
  "level": "ERROR",
  "message": "Failed to connect to database",
  "service": "user-service",
  "database": "postgres-primary",
  "request_id": "abc-123",
  "trace_id": "xyz-789",
  "user_id": "user-456"
}
```
Now all questions are easily answerable and the log can be correlated with other logs in the same trace.

## Next Steps

- Day 2: Instead of printing logs, make log collector send logs via HTTP POST to another service. Create a simple HTTP server that receives logs. 
- Day 3: Add buffering to the log collector. Instead of sending logs immediately, have it collect 10 logs and then send batch.
- Day 4: Modify architecture to: collector -> queue -> processor. For now simulate queue with in-memory queue.



