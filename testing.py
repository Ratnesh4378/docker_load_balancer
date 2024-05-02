import requests
import threading
import time
import matplotlib.pyplot as plt

# Function to send multiple requests to the load balancer server
def send_requests(url, num_requests):
    start_time = time.time()
    responses = []

    # Send requests in parallel using threads
    def send_request():
        response = requests.get(url)
        responses.append(response)
    
    threads = []
    for _ in range(num_requests):
        thread = threading.Thread(target=send_request)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    end_time = time.time()

    # Calculate throughput
    total_time = end_time - start_time
    throughput = num_requests / total_time
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Throughput: {throughput:.2f} requests/second")

    # Generate throughput graph
    num_requests_list = list(range(1, num_requests + 1))
    throughput_list = [num_requests / total_time] * num_requests
    plt.plot(num_requests_list, throughput_list)
    plt.xlabel('Number of Requests')
    plt.ylabel('Throughput (requests/second)')
    plt.title('Throughput vs. Number of Requests')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # Load balancer server URL
    load_balancer_url = "http://0.0.0.0:8080"
    # Number of requests to send
    num_requests = 100

    # Send multiple requests to the load balancer server and generate throughput graph
    send_requests(load_balancer_url, num_requests)
