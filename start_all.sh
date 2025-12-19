#!/bin/bash

echo "========================================"
echo "  Starting French Academic AI Chatbot"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    exit 1
fi

echo "[1/4] Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[2/4] Installing backend dependencies (if needed)..."
pip install -q -r requirements.txt

echo "[3/4] Starting backend server..."
gnome-terminal -- bash -c "cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; exec bash" 2>/dev/null || \
xterm -e "cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" 2>/dev/null || \
osascript -e 'tell app "Terminal" to do script "cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"' 2>/dev/null || \
echo "Starting backend in background..." && \
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &

cd ..

echo "[4/4] Starting frontend server..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

gnome-terminal -- bash -c "cd frontend && npm run dev; exec bash" 2>/dev/null || \
xterm -e "cd frontend && npm run dev" 2>/dev/null || \
osascript -e 'tell app "Terminal" to do script "cd frontend && npm run dev"' 2>/dev/null || \
echo "Starting frontend in background..." && \
cd frontend && npm run dev > ../frontend.log 2>&1 &

cd ..

echo ""
echo "========================================"
echo "  Servers Starting..."
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Waiting for servers to start..."
sleep 5

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

echo ""
echo "Servers are running!"
echo "Check the terminal windows or logs (backend.log, frontend.log)"
echo ""

