## Building all docker containers:

#### Step 1: Start the docker-machine and setup the environment variables
```bash
$ cd dockers
$ docker-machine start <your_base_machine> 
$ docker-machine env <your_base_machine>
$ eval "$(docker-machine env <your_base_machine>)"
```
#### Step 2: Build the docker containers and run them.
```bash
$ docker-compose build
$ docker-compose up
```

#### Step 3: Open your browser to view the Dashboard

Use the following URL, only use **Chrome Browser**.
```bash
$ echo "http://$(docker-machine ip <your_base_machine>/profile.html)"
```

#### Step 4: Run your services

Run your services so that they generate data.

```bash
$ cd ../log_replay
$ python replay.py ../test-ms.cfg ../lts-data/flows ../lts-data/ports 84 1
```

With the current data it takes few seconds before it starts projecting the data between different network components. 

## Building individual docker containers:

### Build the redis Docker
```bash
$ docker build -t="redis" .
$ docker run -d --name redis -p 6379:6379 redis
```

### Build the nodeJS Docker
```bash
$ docker build -t="node" .
$ docker run -d --name node -p 8080:8080 --link redis:redis node
```

## List the docker images which are running

```bash
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
73319a1e74a6        apache              "/usr/local/bin/run"     41 minutes ago      Up 27 minutes       0.0.0.0:80->80/tcp       apache
663b59f9a92f        nodejs              "nodemon /src/index.j"   2 hours ago         Up 2 hours          0.0.0.0:8080->8080/tcp   nodejs
d0fd678d7ebf        redis               "/usr/bin/redis-serve"   3 hours ago         Up 3 hours          0.0.0.0:6379->6379/tcp   redis
```

## List the images in docker

```bash
$ docker images 
REPOSITORY          TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
apache              latest              234b4e371c8c        41 minutes ago      268.5 MB
<none>              <none>              9e0075fd0f34        44 minutes ago      268.5 MB
<none>              <none>              eb7371db0895        47 minutes ago      268.5 MB
<none>              <none>              24e2a7182f96        2 hours ago         268.5 MB
<none>              <none>              5fdc8d2cc81d        2 hours ago         268.5 MB
<none>              <none>              cb2e4c5a8fcc        2 hours ago         268.5 MB
nodejs              latest              6d47e5c335f2        2 hours ago         397.5 MB
<none>              <none>              30eccaa62975        2 hours ago         397.5 MB
<none>              <none>              97e86fce0cf9        2 hours ago         397.5 MB
<none>              <none>              66ce8c0b903b        3 hours ago         407.1 MB
<none>              <none>              06318ee0cca1        3 hours ago         268.5 MB
redis               latest              cae381e0c87a        3 hours ago         211.6 MB
ubuntu              14.04               c29e52d44f69        8 days ago          188 MB
```
