# Option 1: Run directly from the project root
uvicorn app.main:app --reload --port 8000

# Option 2: CD into the app directory and run
cd app
uvicorn main:app --reload --port 8000