from app import create_app
from app.extensions import db

app = create_app()

# Test database connection
with app.app_context():
    try:
        connection = db.engine.connect()
        print("Database connection successful!")
        connection.close()
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    app.run(debug=True)
