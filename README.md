# JW-Notes-Merger-Server-V2

JW-Notes-Merger-Server-V2 is a powerful tool designed for merging JW Library's notes, bookmarks, markup, and playlists. This project is an improved version of the original [JW-Notes-Merger-Server](https://github.com/LeomaiaJr/JW-Notes-Merger-Server), now focusing on speed and enhanced support for merging playlists.

## Features

- Fast merging of JW Library databases using FastAPI and SQLite
- Support for merging notes, bookmarks, markup, and playlists
- Improved performance compared to the previous Node.js and Express version
- Docker support for easy deployment

## Project Structure

```

.
├── README.md
├── app
│ ├── merger.py
│ └── server.py
├── base_schema.sql
├── poetry.lock
├── pyproject.toml
├── Dockerfile

```

## Installation and Setup

1. Clone the repository:

```

git clone https://github.com/yourusername/JW-Notes-Merger-Server-V2.git
cd JW-Notes-Merger-Server-V2

```

2. Install dependencies using Poetry:

```

poetry install

```

3. Run the server:

```

poetry run uvicorn app.server:app --reload

```

The server will start running on `http://localhost:8000`.

## API Endpoint

The main endpoint for merging databases is:

- **URL**: `/merge-db`
- **Method**: POST
- **Input**:
- Two files: `main` and `toMerge`
- **Response**: A merged database file

Note: The endpoint names and field names have been kept the same as the previous version for compatibility with the existing front-end.

## Docker Support

To build and run the Docker container:

1. Build the Docker image:

```

docker build -t jw-notes-merger-v2 .

```

2. Run the Docker container:

```

docker run -p 8000:8000 jw-notes-merger-v2

```

The server will be accessible at `http://localhost:8000`.
