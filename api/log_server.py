#!/usr/bin/env python3
"""
Simple Log Server
Receives structured log batches via HTTP POST and displays them
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# In-memory storage for received logs
received_logs = []


@app.route('/log', methods=['POST'])
def receive_log():
    """
    Endpoint to receive log batches via HTTP POST.

    Expected JSON format:
    {
        "logs": [
            {
                "timestamp": "2026-04-29T05:35:40.039540Z",
                "level": "INFO",
                "message": "user login success"
            }
        ]
    }
    """
    try:
        payload = request.get_json()

        if not payload:
            return jsonify({"error": "No JSON data provided"}), 400

        log_batch = payload.get("logs")

        if not isinstance(log_batch, list) or not log_batch:
            return jsonify({"error": "Expected a non-empty 'logs' array"}), 400

        required_fields = ["timestamp", "level", "message"]

        for index, log_data in enumerate(log_batch):
            if not isinstance(log_data, dict):
                return jsonify({
                    "error": f"Log at index {index} must be an object"
                }), 400

            missing_fields = [field for field in required_fields if field not in log_data]

            if missing_fields:
                return jsonify({
                    "error": f"Log at index {index} is missing required fields: {', '.join(missing_fields)}"
                }), 400

        received_logs.extend(log_batch)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received batch of {len(log_batch)} logs:")
        print(json.dumps(log_batch, indent=2))
        print("-" * 60)

        return jsonify({
            "status": "success",
            "message": f"Batch received successfully",
            "logs_received": len(log_batch)
        }), 200

    except Exception as e:
        print(f"Error processing log batch: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Endpoint to retrieve all received logs.
    """
    return jsonify({
        "total": len(received_logs),
        "logs": received_logs
    }), 200


@app.route('/logs/count', methods=['GET'])
def get_log_count():
    """
    Endpoint to get the count of received logs.
    """
    return jsonify({
        "count": len(received_logs)
    }), 200


@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """
    Endpoint to clear all received logs.
    """
    global received_logs
    count = len(received_logs)
    received_logs = []
    return jsonify({
        "status": "success",
        "message": f"Cleared {count} logs"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({
        "status": "healthy",
        "service": "log-server",
        "logs_received": len(received_logs)
    }), 200


def main():
    """Main entry point for the log server."""
    print("=" * 60)
    print("Log Server Starting")
    print("=" * 60)
    print("Endpoints:")
    print("  POST   /log          - Receive log batches")
    print("  GET    /logs         - Retrieve all logs")
    print("  GET    /logs/count   - Get log count")
    print("  POST   /logs/clear   - Clear all logs")
    print("  GET    /health       - Health check")
    print("=" * 60)
    print("Server running on http://localhost:8080")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=False)


if __name__ == "__main__":
    main()

# Made with Bob