#!/bin/bash
# Script to run tests on Linux/Mac

echo "Running tests..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "Test coverage report generated in htmlcov/index.html"

