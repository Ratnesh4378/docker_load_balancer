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


