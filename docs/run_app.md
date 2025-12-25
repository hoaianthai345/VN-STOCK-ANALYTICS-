uvicorn backend.app.main:app --reload

# Frontend (dev)
# To use live backend: open a new terminal and run:
cd web
npm run dev

# Or run frontend in mock mode (no backend required):
# Vite exposes environment variables prefixed with VITE_. Set VITE_USE_MOCK=true to enable local mock data.
# Example (macOS / Linux):
VITE_USE_MOCK=true npm run dev
# On Windows (Powershell): $env:VITE_USE_MOCK="true"; npm run dev

