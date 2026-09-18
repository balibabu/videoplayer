from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    print(f"[*] MX Stream server running on http://localhost:{Config.PORT}")
    print(f"[*] Basic Auth Credentials: Username: '{Config.AUTH_USERNAME}' | Password: '{Config.AUTH_PASSWORD}'")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
