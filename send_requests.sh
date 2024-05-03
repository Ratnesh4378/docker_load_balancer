#!/bin/bash

# Define the target URL
URL="http://0.0.0.0:8080"

# Number of requests to send
NUM_REQUESTS=100

# Function to send a single request
send_request() {
    curl -s "$URL"
}

# Send requests in parallel and print the response body
for ((i=0; i<$NUM_REQUESTS; i++)); do
    send_request &
done

# Wait for all requests to finish
wait

echo "All requests sent and responses saved"
