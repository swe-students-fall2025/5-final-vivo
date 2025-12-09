Based on your project files, here's a comprehensive README.md file for your bathroom finder application:

```markdown
# Vivo - NYC Public Bathroom Finder

[![CI](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/webapp-ci.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/webapp-ci.yml)
[![CD](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/docker-cicd.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-vivo/actions/workflows/docker-cicd.yml)

**Live Deployment:** [Your Deployment URL Here]

## Introduction

**Vivo** (meaning "I live" in Latin) is a public bathroom finder and review platform for New York City. The application helps users locate public restrooms throughout NYC, view detailed information about each facility, and contribute reviews and ratings based on their experiences.

Built with Flask and MongoDB, Vivo provides a user-friendly interface for discovering bathroom locations, reading community reviews, and sharing your own feedback. The platform uses real-time data from OpenStreetMap and allows users to authenticate via Google OAuth for a seamless experience.

## Features

- **Google OAuth Authentication**: Secure login using Google accounts
- **Interactive Bathroom Map**: Visual display of all public bathrooms in NYC
- **Bathroom Details & Reviews**: View detailed information and community reviews for each location
- **Review System**: Rate and review bathrooms (0-5 stars with optional comments)
- **Real-time Data**: Bathroom data sourced from OpenStreetMap's Overpass API
- **Responsive Design**: User-friendly interface accessible from any device
- **User Profiles**: Personalized experience with user-specific reviews

## Class Members

- [Your Name Here] ([Your GitHub Username Here])
- [Teammate 2 Name] ([Teammate 2 GitHub Username])
- [Teammate 3 Name] ([Teammate 3 GitHub Username])
- [Teammate 4 Name] ([Teammate 4 GitHub Username])
- [Teammate 5 Name] ([Teammate 5 GitHub Username])

## Architecture

The application consists of two main subsystems:

1. **Flask Web Application** (`app.py`): Main backend server handling API requests, authentication, and business logic
2. **MongoDB Database**: Stores user information, bathroom data, and reviews

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
   Create a `.env` file in the root directory with the following variables:
   ```bash
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>.mongodb.net/<database>?retryWrites=true&w=majority
   FLASK_SECRET_KEY=your_secret_key_here
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

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

1. **Create a `docker-compose.yml` file:**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - MONGO_URI=${MONGO_URI}
         - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
         - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
         - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
       volumes:
         - .:/app
   ```

2. **Create a `Dockerfile` in the root directory:**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   ENV FLASK_APP=app.py
   ENV FLASK_RUN_HOST=0.0.0.0
   
   EXPOSE 8000
   
   CMD ["python", "app.py"]
   ```

3. **Run with Docker Compose:**
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

## API Endpoints

### Authentication
- `GET /login` - Login page
- `GET /login/google` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback endpoint
- `GET /logout` - Logout user

### Bathroom Data
- `GET /api/bathrooms` - Get basic bathroom data (coordinates only)
- `GET /api/bathrooms/full` - Get complete bathroom data with reviews
- `GET /api/bathrooms/<osm_id>` - Get details for specific bathroom
- `POST /api/bathrooms/add` - Add new bathroom (admin only)

### Reviews
- `GET /api/bathrooms/<osm_id>/reviews` - Get reviews for specific bathroom
- `POST /api/bathrooms/<osm_id>/reviews` - Add a review to bathroom

## Testing

Run tests with pytest:

```bash
pytest
```

For test coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

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
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── pyproject.toml         # pytest configuration
├── env.example            # Environment variables template
├── import_overpass.py     # Data import script
├── instructions.md        # Project requirements
├── README.md              # This file
├── tests/                 # Test files
│   └── test_app.py       # Unit tests
└── templates/            # HTML templates
    ├── index.html        # Main page
    └── login.html        # Login page
```

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "email": string,
  "name": string,
  "picture": string,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Bathrooms Collection
```javascript
{
  "osm_id": number,
  "lat": number,
  "lon": number,
  "tags": object,
  "reviews": array,
  "average_rating": number,
  "rating_count": number
}
```

### Review Object
```javascript
{
  "rating": number,
  "comment": string,
  "user_name": string,
  "user_email": string,
  "created_at": datetime
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenStreetMap for providing bathroom data
- Overpass API for querying OpenStreetMap data
- Flask and MongoDB documentation
- Digital Ocean for hosting services
```

This README provides comprehensive documentation for your bathroom finder application. You'll need to:
1. Add your actual deployment URL
2. Add your team members' names and GitHub usernames
3. Add your Docker Hub image links
4. Create the missing files (Dockerfile, docker-compose.yml, tests/)
5. Update the Figma link if you have design files
6. Add a LICENSE file if needed

The README includes all necessary setup instructions, architecture details, API documentation, and deployment guidelines that will help users and developers understand and work with your project.