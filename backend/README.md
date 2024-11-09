# Run the Dockerized application

1. cd into the flask_app folder
2. `docker build -t test-flask-app .`
3. `docker run -p 5001:5001 test-flask-app`

Now your docker container should be running on port 5001.
