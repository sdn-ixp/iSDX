<?php

$services = getenv('VCAP_SERVICES');
$json = json_decode($services, TRUE);

$hostname = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['host'];
$user = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['username'];
$password = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['password'];
$port = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['port'];
$vhost = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['vhost'];

echo "$hostname:$user:$port:$password:$vhost";
?>
