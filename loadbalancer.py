from flask import Flask, request
import requests
import subprocess
import threading
import time
app = Flask(__name__)

# Initialize replicas array
replicas = []
# Lock to protect access to replicas array
lock = threading.Lock()
replicas_updated_event = threading.Event()
def get_replicas():
    # Run docker ps command to get container information
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    
    # Split the output by lines and skip the header line
    lines = result.stdout.split('\n')[1:]

    # Create a list to store replicas sorted by their names
    sorted_replicas = []

    # Iterate over each line to find containers with image "web-all"
    for line in lines:
        if "web-all" in line:
            # Extract the name of the replica from the NAMES column
            replica_name = line.split()[-1]
            # Extract the port from the PORTS column
            port = line.split("->")[0].split(":")[-1]
            sorted_replicas.append((replica_name, f'http://localhost:{port}'))

    # Sort the replicas by their names
    sorted_replicas.sort()

    # Clear the replicas list before updating
    replicas.clear()

    # Append the sorted replicas to the replicas list
    for _, replica_url in sorted_replicas:
        replicas.append(replica_url)


def scale_listener():
    while True:
        scale_command = input("Enter scale command (e.g., 'docker-compose -f compose.yaml up --scale web=<number_of_replicas>'): ")
        if "docker compose" in scale_command and "--scale web=" in scale_command:
            # Acquire lock before updating replicas array
            with lock:
                # Extract the number of replicas from the scale command
                num_replicas = int(scale_command.split("--scale web=")[1])
                # Scale the "web" service using Docker Compose
                scale_command += " &"
                subprocess.run(scale_command, shell=True)
                print(f"Ran the subprocess: {scale_command}")
                # Wait until the server starts running
                print("Waiting for server to start...")
                server_started = False
                while not server_started:
                    # Check the number of running containers for "web-all" image
                    ps_command = subprocess.Popen(['docker', 'ps'], stdout=subprocess.PIPE)
                    grep_command = subprocess.Popen(['grep', 'web-all'], stdin=ps_command.stdout, stdout=subprocess.PIPE)
                    wc_command = subprocess.Popen(['wc', '-l'], stdin=grep_command.stdout, stdout=subprocess.PIPE)
                    ps_command.stdout.close()  # Allow ps_command to receive a SIGPIPE if grep_command exits.
                    grep_command.stdout.close()  # Allow grep_command to receive a SIGPIPE if wc_command exits.
                    num_running_containers = int(wc_command.communicate()[0].strip())
                    if num_running_containers == num_replicas:
                        server_started = True
                    else:
                        # Server is not yet running, wait for a moment and retry
                        time.sleep(1)
                print("Server started successfully.")
                # Update the replicas array
                get_replicas()
                print("Replicas updated:", replicas)

# Start a separate thread to listen for scaling commands
scale_thread = threading.Thread(target=scale_listener)
scale_thread.start()

# Index to keep track of the next replica to use
current_replica = 0
i=0
@app.route('/')
def index():
    global current_replica
    global replicas
    global i

    # Acquire lock before accessing replicas array
    with lock:
        # Select the next replica in a round-robin fashion
        # i+=1
        # if i==2:
        #     time.sleep(100)

        print(f"========== {current_replica}==========")
        get_replicas()
        print(f"Replicas:{replicas}")
        print(f"Length of replicas:{len(replicas)}")
        if current_replica>=len(replicas):
            current_replica=0
        current_replica=current_replica%len(replicas)
        replica_url = replicas[current_replica]
        current_replica = (current_replica + 1) % len(replicas)
    
    # Forward the request to the selected replica
    response = requests.get(replica_url + request.full_path)
    return response.content, response.status_code, response.headers.items()

if __name__ == '__main__':
    # Initialize replicas array
    get_replicas()
    app.run(debug=True,threaded=True)
