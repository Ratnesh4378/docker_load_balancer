from flask import Flask, request
import requests
import subprocess
import threading
import time
app = Flask(__name__)

# Initialize replicas array
replicas = []
replica_requests = {}
# Lock to protect access to replicas array
lock = threading.Lock()
cond=threading.Condition()
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
    with cond:
        for _, replica_url in sorted_replicas:
            replicas.append(replica_url)
            if replica_url not in replica_requests:
                    replica_requests[replica_url] = 0
        
        for replica_url in list(replica_requests.keys()):
            if replica_url not in [r[1] for r in sorted_replicas]:
                del replica_requests[replica_url]

'''
def scale_listener():
    while True:
        scale_command = input("Enter scale command (e.g., 'docker compose -f compose.yaml up --scale web=<number_of_replicas>'): ")
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
'''
def scale_listener():
    global replicas
    while True:
        # Check the total number of active connections
        total_active_connections = 0
        with cond:
            for request_count in replica_requests.values():
                total_active_connections += request_count
        
        # Determine if scaling is needed
        get_replicas()
        if total_active_connections >=len(replicas):
            # Scale up
            scale_command = f"docker compose -f compose.yaml up --scale web={len(replicas)+1}"
            subprocess.run(scale_command, shell=True)
            print(f"Scaling up with command: {scale_command}")
        elif len(replicas)>3:
            # Scale down
            scale_command = f"docker compose -f compose.yaml up --scale web={len(replicas)-1}"
            subprocess.run(scale_command, shell=True)
            print(f"Scaling down with command: {scale_command}")
        else:
            # No scaling needed
            print("No scaling needed")
        
        # Wait for a certain interval before checking again
        time.sleep(5)  # Adjust the interval as needed


# Start a separate thread to listen for scaling commands
scale_thread = threading.Thread(target=scale_listener)
scale_thread.start()

# Index to keep track of the next replica to use
current_replica = 0
i=0


def get_least_connection_replica():
    with lock:
        least_connection_replica = min(replicas, key=lambda x: x[1])[0]
        return least_connection_replica

@app.route('/')
def index():
    '''
    global current_replica
    global replicas
    global replica_requests
    global i

    # Acquire lock before accessing replicas array
    with lock:
        # Select the next replica in a round-robin fashion
        # i+=1
        # if i==2:
        #     time.sleep(100)
        get_replicas()
        print(f"========== {current_replica}=={len(replica_requests)}==========")
        print(f"Replicas:{replicas}")
        print(f"Length of replicas:{len(replicas)}")
        if current_replica>=len(replicas):
            current_replica=0
        current_replica=current_replica%len(replicas)
        replica_url = replicas[current_replica]
        current_replica = (current_replica + 1) % len(replicas)
        replica_requests[replica_url] += 1
    
    # Forward the request to the selected replica
    response = requests.get(replica_url + request.full_path)
    with lock:
        replica_requests[replica_url] -= 1
    return response.content, response.status_code, response.headers.items()
    '''
    global replicas
    global replica_requests
    # Acquire condition lock
    with cond:
        get_replicas()
        # Check if replicas are available
        if not replicas:
            return "No replicas available", 503
        # Sort replica_requests based on active connections
        sorted_replicas = sorted(replica_requests.items(), key=lambda x: x[1])
        
        # Select the replica with the least number of active connections
        least_connection_replica = sorted_replicas[0][0]
        replica_requests[least_connection_replica] += 1
        # Forward the request to the selected replica
        response = requests.get(least_connection_replica + request.full_path)
        replica_requests[least_connection_replica] -=1

    # Return the response
    print(f"======{least_connection_replica}========")
    return response.content, response.status_code, response.headers.items()



@app.route("/least_connection")
def least_connection():
    pass
    


if __name__ == '__main__':
    # Initialize replicas array
    get_replicas()
    app.run(debug=True,threaded=True)
