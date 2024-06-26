import time
import redis
import socket
from flask import Flask
from prometheus_client import Counter, generate_latest, REGISTRY
from flask import Response



app = Flask(__name__)
cache = redis.Redis(host='redis', port=6379)

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError as exc:
            if retries == 0:
                raise exc
            retries -= 1
            time.sleep(0.5)

# Expose a Prometheus metrics endpoint
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype="text/plain")


@app.route('/')
def hello():
    count = get_hit_count()
    time.sleep(1)
    return 'hey !! Hello World! I have been seen {} times.Hostname: {}\n'.format(count,socket.gethostname())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

#14b5076391b1
#f468f9f6ad26
#aeadea41b938