#!/bin/bash
# Run all RAG tests with proper setup

cd "$(dirname "$0")/.."

echo "=========================================="
echo "RAG Test Suite"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Check if services are running
echo "Checking services..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠ MCP Server not running. Start services first:"
    echo "   ./scripts/start_services.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Clear Milvus database
echo "=========================================="
echo "Clearing Milvus Database"
echo "=========================================="
python -c "
import sys
sys.path.insert(0, '.')
from services.milvus_client import MilvusClient
from config.settings import get_settings

settings = get_settings()
client = MilvusClient(settings)
try:
    client.clear_collection()
    print('✓ Milvus database cleared')
except Exception as e:
    print(f'⚠ Could not clear Milvus: {e}')
"
echo ""

# Run tests
echo "=========================================="
echo "Running Tests"
echo "=========================================="
echo ""

# Run with pytest
pytest tests/ -v --tb=short --log-cli-level=INFO

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "=========================================="

exit $TEST_EXIT_CODE

# Made with Bob
