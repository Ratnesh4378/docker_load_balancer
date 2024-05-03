from flask import Flask, request
import requests
import subprocess
import threading
import time

import logging
import random
app = Flask(__name__)

# Initialize replicas array

replicas = []
replica_requests = {}
replicas_prob={}
list_of_prob=[1,3,5,7,9,11,13,15,17,19]
x=0

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

            if replica_url not in replicas_prob:
                random_num = random.choice(list_of_prob)
                replicas_prob[replica_url] = random_num
                list_of_prob.remove(random_num)
        store_req=[]
        for replica_url in list(replica_requests.keys()):
            if replica_url not in [r[1] for r in sorted_replicas]:
                store_req.append(replica_url)
                del replica_requests[replica_url]
        
        if(len(store_req)):
            for i in store_req:
                list_of_prob.append(replicas_prob[i])
                del replicas_prob[i]

    

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
        if(x==0):
            if total_active_connections >=len(replicas):
                # Scale up
                scale_command = f"docker compose -f compose.yaml up -d --scale web={len(replicas)+1}"
                subprocess.run(scale_command, shell=True)
                print(f"Scaling up with command: {scale_command}")
            elif len(replicas)>3:
                # Scale down
                scale_command = f"docker compose -f compose.yaml up -d --scale web={len(replicas)-1}"
                subprocess.run(scale_command, shell=True)
                print(f"Scaling down with command: {scale_command}")
            else:
                # No scaling needed
                print("No scaling needed")
        else:
            if total_active_connections >=len(replicas_prob) and len(replicas_prob)<=10:
                # Scale up
                scale_command = f"docker compose -f compose.yaml up --scale web={len(replicas)+1}"
                subprocess.run(scale_command, shell=True)
                print(f"Scaling up with command: {scale_command}")
            elif len(replicas_prob)>3:
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
#scale_thread = threading.Thread(target=scale_shared_listener)
scale_thread.start()

# Index to keep track of the next replica to use
# current_replica = 0
# i=0


# def get_least_connection_replica():
#     with lock:
#         least_connection_replica = min(replicas, key=lambda x: x[1])[0]
#         return least_connection_replica

# #the following code is for least connection protocol

# @app.route('/')
# def index():
#     global current_replica
#     global i
#     global replicas
#     # Acquire condition lock
#     with lock:
#         get_replicas()
#         # Check if replicas are available
#         if not replicas:
#             return "No replicas available", 503
#         # Sort replica_requests based on active connections
#         sorted_replicas = sorted(replica_requests.items(), key=lambda x: x[1])
        
#         # Select the replica with the least number of active connections
#         least_connection_replica = sorted_replicas[0][0]
#         replica_requests[least_connection_replica] += 1
#         # Forward the request to the selected replica
#     response = requests.get(least_connection_replica + request.full_path)

#     with lock:
#         replica_requests[least_connection_replica] -=1

#     # Return the response
#     return response.content, response.status_code, response.headers.items()


#the following code is for round robin
  
# @app.route('/')
# def index():
#     global current_replica
#     global i
#     global replicas
#     # Acquire lock before accessing replicas array
#     with lock:
#         # Select the next replica in a round-robin fashion
#         # i+=1
#         # if i==2:
#         #     time.sleep(100)
#         get_replicas()
#         print(f"========== {current_replica}=={len(replica_requests)}==========")
#         print(f"Replicas:{replicas}")
#         print(f"Length of replicas:{len(replicas)}")
#         if current_replica>=len(replicas):
#             current_replica=0
#         current_replica=current_replica%len(replicas)
#         replica_url = replicas[current_replica]
#         current_replica = (current_replica + 1) % len(replicas)
#         replica_requests[replica_url] += 1
    
#     # Forward the request to the selected replica
#     response = requests.get(replica_url + request.full_path)
#     with lock:
#         replica_requests[replica_url] -= 1
#     return response.content, response.status_code, response.headers.items()



#the following code is for probabilistic load distribution

@app.route('/')
def index():
    global replicas_prob
    global x 
    x=1
    
    with lock:
    # Calculate total weight of all replicas
        total_weight = sum(replicas_prob.values())
        logging.info(replicas_prob.values())


        # Calculate probability distribution
        probabilities = {replica: weight / total_weight for replica, weight in replicas_prob.items()}

        # Generate random number between 0 and 1
        rand = random.random()

        # Determine which replica the random number falls into
        cumulative_prob = 0
        for replica, prob in probabilities.items():
            cumulative_prob += prob
            if rand < cumulative_prob:
                replica_url = replica
                break
        replica_requests[replica_url] += 1


    # Forward the request to the selected replica
    response = requests.get(str(replica_url) + request.full_path)
    with lock:
        replica_requests[replica_url] -= 1
    return response.content, response.status_code, response.headers.items()
    


if __name__ == '__main__':
    # Initialize replicas array
    get_replicas()
    app.run(debug=True,threaded=True)
