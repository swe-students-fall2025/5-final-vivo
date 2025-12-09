# NYC Public Bathroom Finder

A web application that helps users locate public bathrooms in New York City using real-time OpenStreetMap data. The system consists of a Flask web application, a Leaflet-based frontend that displays bathroom locations, and an integrated sidebar that shows bathroom details, images, and comments.

## Features

- **Real-Time Bathroom Retrieval**: Uses Overpass API to fetch all public bathroom locations in NYC based on OpenStreetMap data.
- **Interactive Leaflet Map**: Includes marker clustering, NYC-bounded geocoding, and dynamic marker rendering.
- **Bathroom Detail Sidebar**: View bathroom name, address, upload a photo (client-side preview), and add comments.
- **Google OAuth Login**: Secure login using Google OAuth 2.0 with user profile display.
- **Responsive UI**: Sidebar, map, and user elements adapt to desktop layouts.

## Team Members

- [Maria Lee](https://github.com/MariaLuo826)￼

## Architecture

The system consists of three main components:

1. **Flask Web Application** (`web-app/`): Handles routing, Google OAuth login, rendering HTML templates, and serving static resources.
2. **Leaflet Map Frontend** (`webapp/static/`): Renders an interactive NYC map, retrieves bathroom data, displays markers, and manages sidebar interactions.
3. **Overpass API Integration**: Dynamically retrieves bathroom locations from OpenStreetMap using a custom Overpass query.

## Prerequisites

- Python 3.10+
- Git
- Google Cloud OAuth Credentials (Client ID and Secret)
-Docker and Docker Compose installed

## Quick Start

### Using Local Python Environment (Recommended)

1.	Clone the repository:
    ```bash
    git clone <repository-url>
    cd 5-final-vivo
    ```


2.	Install dependencies:

    pip install -r requirements.txt


3.	Create a .env file in the project root:

    FLASK_SECRET_KEY=your-secret-key
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret


4.	Run the Flask application:

    python3 webapp/app.py


5.	Open the web application:

    http://127.0.0.1:5000



## Overpass API Query Used

[out:json][timeout:25];
area["name"="City of New York"]["boundary"="administrative"]["admin_level"="5"]->.nyc;
(
  node["amenity"="toilets"](area.nyc);
  way["amenity"="toilets"](area.nyc);
  relation["amenity"="toilets"](area.nyc);
);
out center;

## Environment Variables

FLASK_SECRET_KEY	Flask application secret key
GOOGLE_CLIENT_ID	Google OAuth client ID
GOOGLE_CLIENT_SECRET	Google OAuth client secret

### Example .env File

FLASK_SECRET_KEY=mysecretkey123
GOOGLE_CLIENT_ID=myclientid.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=myclientsecret

Notes:
	•	.env is ignored by Git for security.
	•	OAuth callback URL must match your Google Cloud configuration.

## Project Structure

5-final-vivo/
├── webapp/
│   ├── app.py                # Flask backend
│   ├── requirements.txt      # Dependencies
│   ├── static/
│   │   ├── home.js           # Map and sidebar logic
│   │   └── home.css          # Styling
│   └── templates/
│       └── index.html        # Frontend template with Leaflet sidebar
├── .env                      # Environment variables (ignored by Git)
└── README.md

## API Endpoints

### Web Application

- GET / – Main map interface
- GET /login – Google OAuth login
- GET /logout – Logout and clear session
- GET /auth/callback – OAuth callback handler

## Map and Sidebar Functionality

### Map Features
- NYC-centered Leaflet map
- Marker clustering for performance
- NYC-limited search (via Leaflet Control Geocoder)
- Dynamic marker creation from Overpass API results

### Sidebar Features
- Displays name and address when clicking a bathroom marker
- Supports client-side photo upload (preview only)
- Per-bathroom comment system (stored in-memory during session)

## Troubleshooting

### Google OAuth Issues

If login fails:
1.	Verify your redirect URI in Google Cloud Console matches:
    
    http://127.0.0.1:5000/auth/callback


2.	Ensure your .env contains valid client ID and secret.

### Sidebar Not Working

Ensure the following script is loaded before home.js:

<script src="https://unpkg.com/leaflet-sidebar-v2@3.2.0/js/leaflet-sidebar.min.js"></script>
