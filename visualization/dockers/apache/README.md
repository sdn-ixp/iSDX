## Healthcheck Widget Docker

### Step 1: Checkout the Hawkeye-Healthcheck widget code:

```bash
$ cd heathcheck-apache-dpc/apache-php/implementation/docker/apache-php

$ ls
apache_default  container.json  Dockerfile  hawkeye-portal-healthcheck  LICENSE  README.md  run

# the hawkeye-portal might be empty
$ ls hawkeye-portal-healthcheck

# checkout the code from repository
$ git clone http://10.245.12.194/pawara1/hawkeye-portal-healthcheck.git
```

### Step 2: Build the Docker image

```bash
$ docker build -t apache-hc .
$ docker images
REPOSITORY            TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
apache-hc             latest              a11a4c654f6d        3 hours ago         268.6 MB
ubuntu                raring              463ff6be4238        16 months ago       169.3 MB

```

### Step 3: Run the Docker image
```bash
$ docker run -d -p 80:80 apache-hc
$ docker ps
CONTAINER ID        IMAGE                     COMMAND                CREATED             STATUS              PORTS                                               NAMES
22ce0a4878ba        apache-hc:latest          "/usr/local/bin/run"   5 minutes ago       Up 5 minutes        0.0.0.0:80->80/tcp                                  sad_wilson          
e1c10ea9f0dc        tobert/cassandra:latest   "/bin/cassandra-dock   2 weeks ago         Up 2 weeks          7000/tcp, 7199/tcp, 9042/tcp, 9160/tcp, 61621/tcp   nostalgic_meitner   
c3d49aa02c46        cpsredis:latest           "/usr/bin/redis-serv   2 weeks ago         Up 2 weeks          0.0.0.0:6379->6379/tcp                              gloomy_mclean       
c30e02539082        cpsrabbit:latest          "/docker-entrypoint.   2 weeks ago         Up 2 weeks          0.0.0.0:5672->5672/tcp, 0.0.0.0:8888->15672/tcp     thirsty_thompson    
e41f3ba70732        discovery:latest          "./startDiscoverySvc   2 weeks ago         Up 2 weeks          0.0.0.0:8084->8084/tcp                              elated_bartik    
```