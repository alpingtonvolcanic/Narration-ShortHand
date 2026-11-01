import os

from app import app

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "").lower() == "true",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
    )
