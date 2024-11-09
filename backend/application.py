# This file runs the Flask app
# It initializes all of the endpoints and runs the server
# you can connect to the server for testing by going to: 
# http://localhost:5000/YOUR_ENDPOINT
from app import create_app

application = create_app()

if __name__ == '__main__':
    # Run the app
    application.run(host='0.0.0.0', port=3000, debug=True)