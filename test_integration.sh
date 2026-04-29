#!/bin/bash
# Integration test script for Day 2

echo "=========================================="
echo "Day 2 Integration Test"
echo "=========================================="
echo ""

# Start the log server in the background
echo "1. Starting log server..."
python3 api/log_server.py &
SERVER_PID=$!

# Wait for server to start
echo "   Waiting for server to start..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "   ✗ Server failed to start"
    exit 1
fi
echo "   ✓ Server started (PID: $SERVER_PID)"
echo ""

# Test health endpoint
echo "2. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
echo "   Response: $HEALTH_RESPONSE"
echo ""

# Run the log collector
echo "3. Running log collector..."
python3 collector/log_collector.py collector/sample_logs.txt
echo ""

# Get log count
echo "4. Checking received logs..."
LOG_COUNT=$(curl -s http://localhost:8080/logs/count | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
echo "   Logs received: $LOG_COUNT"
echo ""

# Retrieve all logs
echo "5. Retrieving all logs..."
curl -s http://localhost:8080/logs | python3 -m json.tool
echo ""

# Cleanup
echo "6. Cleaning up..."
kill $SERVER_PID 2>/dev/null
echo "   ✓ Server stopped"
echo ""

echo "=========================================="
echo "Test Complete!"
echo "=========================================="

# Made with Bob
