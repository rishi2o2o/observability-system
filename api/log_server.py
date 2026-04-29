#!/usr/bin/env python3
"""
Simple Log Server
Receives structured logs via HTTP POST and displays them
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
    Endpoint to receive log entries via HTTP POST.
    
    Expected JSON format:
    {
        "timestamp": "2026-04-29T05:35:40.039540Z",
        "level": "INFO",
        "message": "user login success"
    }
    """
    try:
        log_data = request.get_json()
        
        if not log_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ["timestamp", "level", "message"]
        missing_fields = [field for field in required_fields if field not in log_data]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Store the log
        received_logs.append(log_data)
        
        # Print the received log to console
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received log:")
        print(json.dumps(log_data, indent=2))
        print("-" * 60)
        
        return jsonify({
            "status": "success",
            "message": "Log received successfully"
        }), 200
        
    except Exception as e:
        print(f"Error processing log: {e}")
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
    print("  POST   /log          - Receive log entries")
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