# FastAPI Project

A basic FastAPI project with SQLAlchemy and Pydantic.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your database:
- Make sure PostgreSQL is installed and running
- Create a database named `fastapi_db`
- Update the `.env` file with your database credentials if needed

## Running the Application

Start the application with:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Available Endpoints

- `GET /`: Welcome message
- `POST /api/v1/items/`: Create a new item
- `GET /api/v1/items/`: List all items
- `GET /api/v1/items/{item_id}`: Get a specific item 