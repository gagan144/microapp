FROM python:3.6-slim

# Install linux dependencies
#RUN apt update && apt --yes install build-essential cmake libgtk-3-dev libboost-all-dev && apt clean && rm -rf /tmp/* /var/tmp/*

# Set working directory
WORKDIR '/app'

# Install python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip cache purge

# Setup application
COPY . .
RUN mkdir logs

# Set Environment variables
ENV APP_PORT=7000

# Run server
CMD uvicorn microapp:app --host=0.0.0.0 --port=$APP_PORT --workers=3 --log-config=log_config.json --timeout-keep-alive=10
