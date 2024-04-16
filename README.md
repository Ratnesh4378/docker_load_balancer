# docker_load_balancer
Load balancer to schedule incoming requests appropriately to different containers of the same docker image.


## -------Steps to run------------##

## Step 1

docker compose -f compose.yaml up --scale web=[NO_OF_REPLICAS]

## Step 2

docker ps

Observe the port numbers exposed by the web containers

## Step 3

from host side at the web browser browse:

localhost:<Port-no-of-web-image>

## -------Steps to stop------------## 

(We need to stop the containers before running them again)

open another terminal and run:
docker compose down