# Vivo - NYC Public Bathroom Finder

[![CI](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/webapp-ci.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/webapp-ci.yml)
[![CD](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/docker-cicd.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/docker-cicd.yml)

**Live Deployment:** [Your Deployment URL Here]

## Introduction

**Di2** is a public bathroom finder and review platform for New York City. The application helps users locate public restrooms throughout NYC, view detailed information about each facility, and contribute reviews and ratings based on their experiences.

Built with Flask and MongoDB, Di2 provides a user-friendly interface for discovering bathroom locations, reading community reviews, and sharing your own feedback. The platform uses real-time data from OpenStreetMap and allows users to authenticate via Google OAuth for a seamless experience.

## Features

- **Search for Bathrooms**: Find public restrooms throughout New York City
- **View Bathroom Details**: See comprehensive information about each bathroom facility
- **Add Reviews**: Share your experience by writing reviews for bathrooms you've visited
- **Rate Bathrooms**: Give star ratings (0-5) to help others find quality facilities
- **Add New Bathrooms**: Contribute to the community by adding missing bathrooms to the database
- **Google Login**: Secure authentication using your Google account

## Group Members

- [Maria Lee] ([https://github.com/MariaLuo826])
- [Natalie Han] ([https://github.com/nateisnataliehan])
- [Teammate 3 Name] ([Teammate 3 GitHub Username])
- [Teammate 4 Name] ([Teammate 4 GitHub Username])
- [Teammate 5 Name] ([Teammate 5 GitHub Username])

## Setup and Installation

### Prerequisites

- Python 3.8+
- MongoDB Atlas account or local MongoDB instance
- Google OAuth credentials (Google Cloud Console)
- Docker and Docker Compose (optional)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/swe-students-fall2025/5-final-vivo.git
   cd 5-final-vivo
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp env.example .env
   ```
   Edit the `.env` file and replace the placeholder values with your actual credentials.

5. **Import bathroom data:**
   ```bash
   python import_overpass.py
   ```
   This will fetch and populate NYC bathroom data from OpenStreetMap.

6. **Run the application:**
   ```bash
   python app.py
   ```
   The application will be available at `http://localhost:5000`

### Docker Setup

To run the application using Docker Compose:

1. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   The application will be available at `http://localhost:8000`

## Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client IDs"
5. Configure the OAuth consent screen
6. Add authorized redirect URIs:
   - For local development: `http://localhost:5000/auth/callback`
   - For production: `https://your-domain.com/auth/callback`
7. Copy the Client ID and Client Secret to your `.env` file

## API Routes

### Authentication Routes
- `GET /` - Home page (requires login)
- `GET /login` - Login page
- `GET /login/google` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback endpoint
- `GET /logout` - Logout user

### Bathroom API Routes
- `GET /api/bathrooms` - Get basic bathroom data (coordinates only)
- `GET /api/bathrooms/full` - Get complete bathroom data with reviews
- `GET /api/bathrooms/<osm_id>` - Get details for specific bathroom
- `POST /api/bathrooms/add` - Add new bathroom

### Review API Routes
- `GET /api/bathrooms/<osm_id>/reviews` - Get reviews for specific bathroom
- `POST /api/bathrooms/<osm_id>/reviews` - Add a review to bathroom

## Deployment

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. **CI Workflow** (`webapp-ci.yml`):
   - Runs on push to main branch
   - Installs dependencies
   - Runs tests and coverage checks
   - Builds Docker image

2. **CD Workflow** (`docker-cicd.yml`):
   - Triggers after successful CI
   - Pushes Docker image to Docker Hub
   - Deploys to Digital Ocean

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

| Secret                      | Description                      |
| --------------------------- | -------------------------------- |
| `DOCKERHUB_USERNAME`        | Docker Hub username              |
| `DOCKERHUB_TOKEN`           | Docker Hub personal access token |
| `DIGITALOCEAN_ACCESS_TOKEN` | Digital Ocean API token          |
| `MONGO_URI`                 | MongoDB connection string        |
| `FLASK_SECRET_KEY`          | Flask application secret key     |
| `GOOGLE_CLIENT_ID`          | Google OAuth client ID           |
| `GOOGLE_CLIENT_SECRET`      | Google OAuth client secret       |

### Digital Ocean Deployment

1. Create a Digital Ocean App
2. Connect your GitHub repository
3. Configure environment variables
4. Deploy from the main branch

## Project Structure

```
5-final-vivo/
├── .githooks/
│   └── commit-msg
├── .github/
│   └── workflows/
│       ├── webapp-ci.yml
│       ├── docker-cicd.yml
│       └── event-logger.yml
├── webapp/                        # Main Flask backend application
│   ├── app.py                     # Flask entry point
│   ├── Dockerfile                 # Docker configuration
│   ├── requirements.txt           # Flask backend dependencies
│   ├── static/                    # Frontend static assets
│   │   ├── app.js
│   │   ├── home.css
│   │   ├── home.js
│   │   ├── img/
│   │   │   ├── bg.png
│   │   │   ├── cluster.png
│   │   │   ├── default.png
│   │   │   └── toilet.png
│   │   ├── plastic_toilet_cabin.glb
│   │   ├── script.js
│   │   └── style.css
│   └── templates/                 # HTML templates
│       ├── index.html
│       └── login.html
├── tests/                         # Backend unit tests
│   ├── __init__.py
│   └── test_backend.py
├── docker-compose.yml     # Docker Compose configuration
├── env.example            # Environment variables template
├── .gitignore            # Git ignore rules
├── import_overpass.py     # Data import script
├── instructions.md       
├── LICENSE       
├── pyproject.toml        # pytest configuration
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── Pipfile       
├── Pipfile.lock     
├── pytest.ini           # Pytest settings
└── note.txt    
```
