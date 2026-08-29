"""
app.py
=======================================================
JARVIS - Flask application entry point.

Run:
    pip install -r requirements.txt
    cp .env.example .env   # then fill in GEMINI_API_KEY etc.
    python app.py
"""

from flask import Flask, render_template
from config import Config
from routes.api import api_bp
from utils.logger import get_logger

logger = get_logger("jarvis.app")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {"status": "online", "assistant": "JARVIS"}

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Starting JARVIS...")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
