@echo off

echo Starting frontend server...
start cmd /k "cd frontend && npm start"

echo Starting backend server...
start cmd /k "cd backend && python app.py"
