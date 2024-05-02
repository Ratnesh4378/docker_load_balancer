# docker_load_balancer
Load balancer to schedule incoming requests appropriately to different containers of the same docker image.


## -------Steps to run------------

## Step 1

docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]

## Step 2
open another terminal

docker ps

Observe the port numbers exposed by the web containers

## Step 3

from host side at the web browser browse:

localhost:[Port-no-of-web-image]

## -------Steps to stop------------

(We need to stop the containers before running them again)

open another terminal and run:

docker compose -f compose.yaml down


## -------How to run Load Balancer------------

Either you can run : docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS] , or You can directly run : python3 loadbalancer.py

### case 1: First you ran docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]

In this case, you run:\
python3 loadbalancer.py 

As and when outputs become stable in loadbalancer terminal, then you can scale the replicas by running the following command in the loadbalancer terminal:\
docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]


### case 2: You can run , python3 loadbalancer.py

In this case , you need to run the following command to start the web server containers:\
docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]

After this you can scale the replicas anytime, by running the following command in the loadbalancer terminal:\
docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]

To run with gunicorn:\
gunicorn --config gunicorn_config.py loadbalancer:app


NOTE: In either cases, while scaling , when you provide the number of replicas , these are the replicas you need to run currently:\
For eg. if 3 web servers are running currently , and you need to add one more server then you need to run the following command:\
docker compose -f compose.yaml up --scale web=4

And if you want to remove one server then you need to run:\
docker compose -f compose.yaml up --scale web=2



## ------- Future Step ------------

services:
  web:
    image: "web-all"
    build: .
    ports:
      - "0:5000"
  load_balancer:    [Add-This-Load-Balancer-server-image]
    ports:
      - "80:80"     [Port-80-exposed-to-poprt-80]

  redis:
    image: "redis:alpine"
 
## See expected.yaml for more idea

## create a separate flask server for load-balancer, and with the help of Dockerfile, build the image for the load-balancer server
See how we created Dockerfile to build an image for for app.py

Note: There will be only one Dockerfile , which will run app.py as well as load_balancer.py
Two Dockerfile can't be there.

## Protocols to be used for load balancer: round-robin, probalistic, and one more (choose any from the internet)


