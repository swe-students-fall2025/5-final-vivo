import os
from flask import Flask
from extensions import oauth
from routes import auth, api, main

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# OAuth Configuration
oauth.init_app(app)
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    api_base_url="https://www.googleapis.com/oauth2/v3/",
    client_kwargs={"scope": "openid email profile"},
)

app.register_blueprint(auth.bp)
app.register_blueprint(api.bp)
app.register_blueprint(main.bp)

if __name__ == "__main__":
    app.run(debug=True)
