from flask import Flask, request
import requests
import subprocess
app = Flask(__name__)

# List of replica URLs

def get_replicas():
    # Run docker ps command to get container information
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    
    # Split the output by lines
    lines = result.stdout.split('\n')
    
    replicas = []
    
    # Iterate over each line to find containers with image "web-all"
    for line in lines[1:]:  # Skip the header line
        if "web-all" in line:
            # Extract the port from the PORTS column
            port = line.split("->")[0].split(":")[-1]
            replicas.append(f'http://localhost:{port}')
    
    return replicas

replicas=get_replicas()
# Index to keep track of the next replica to use
current_replica = 0

@app.route('/')
def index():
    global current_replica
    # Select the next replica in a round-robin fashion
    replica_url = replicas[current_replica]
    current_replica = (current_replica + 1) % len(replicas)
    
    # Forward the request to the selected replica
    response = requests.get(replica_url + request.full_path)
    return response.content, response.status_code, response.headers.items()

if __name__ == '__main__':
    app.run(debug=True)

# from flask import Flask, request
# import requests
# from queue import Queue
# import threading

# app = Flask(__name__)

# # List of replica URLs
# replicas = [
#     'http://localhost:32771',
#     'http://localhost:32772',
#     'http://localhost:32773',
#     # Add more replica URLs as needed
# ]

# # Queue to store incoming requests
# request_queue = Queue()

# # Function to handle forwarding requests from the queue to replicas
# def forward_requests():
#     while True:
#         request_data = request_queue.get()
#         replica_url = replicas.pop(0)
#         replicas.append(replica_url)  # Rotate replicas
#         response = requests.get(replica_url + request_data['path'])
#         print(f"Forwarded request to {replica_url}, response: {response.status_code}")
#         request_queue.task_done()

# # Start a separate thread to handle forwarding requests
# forward_thread = threading.Thread(target=forward_requests)
# forward_thread.daemon = True
# forward_thread.start()

# @app.route('/')
# def index():
#     # Enqueue incoming request
#     request_queue.put({'path': request.full_path})
#     return request.full_path

# if __name__ == '__main__':
#     app.run(debug=True)
