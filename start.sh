#!/bin/bash

# Start script for Open House Matchmaker
set -e

echo "Starting Open House Matchmaker..."
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo "Python path: $PYTHONPATH"

# List contents to verify files are present
echo "Contents of working directory:"
ls -la

# Verify Python can import our modules
echo "Testing module imports..."
python3 -c "
import sys
sys.path.insert(0, '/app')
print('Current Python path:', sys.path[:3])

try:
    from main import app
    print('✓ Successfully imported main.app')
except ImportError as e:
    print('✗ Failed to import main.app:', str(e))
    sys.exit(1)

try:
    from app.api import agents
    print('✓ Successfully imported app.api.agents')
except ImportError as e:
    print('✗ Failed to import app.api.agents:', str(e))
    sys.exit(1)

print('All imports successful!')
"

# Start the server
echo "Starting uvicorn server..."
exec uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000}
