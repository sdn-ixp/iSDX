<?php
require_once(__DIR__ . '/include/util.inc');
require_once(__DIR__ . '/include/db_connect.php');
require_once '/home/vcap/app/lib/vendor/autoload.php';
use PhpAmqpLib\Connection\AMQPConnection;
use PhpAmqpLib\Message\AMQPMessage;

//header('Content-type: text/html');
header('Access-Control-Allow-Origin: *');


$services = getenv('VCAP_SERVICES');
$json = json_decode($services, TRUE);

$hostname = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['host'];
$user = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['username'];
$password = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['password'];
$port = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['port'];
$vhost = $json['p-rabbitmq'][0]['credentials']['protocols']['amqp']['vhost'];

$db = new DB_Connect();
$db->connect();


$system_id = string_escape(util_aiod($_POST, 'ID', ""));
$name = string_escape(util_aiod($_POST, 'name', ""));
$type = 'Thin';
$capacity = string_escape(util_aiod($_POST, 'capacity', ""));
$offset = 0;
$sq = 'gb';
$pool_id = '0';
$sp = string_escape(util_aiod($_POST, 'sp', ""));
$auto_assignment = '1';
$tiering_policy = 'autoTier';
$initial_tier = 'highestAvailable';

$cmd = "naviseccli lun -create -type  " . $type . " -capacity " . $capacity . " -sq " . $sq . " -poolId " . $pool_id . " -sp " . $sp . "  -aa " . $auto_assignment . " -name " . $name . " -offset " . $offset . " -tieringPolicy " . $tiering_policy . " -initialTier " . $initial_tier;

$result = mysql_query("INSERT INTO `requests` (system_id, cmd, type, status) values ('$system_id', '$cmd', 'create_lun', 'N');");

$tuple_id = mysql_insert_id();

$connection = new AMQPConnection($hostname, $port, $user, $password, $vhost);
$channel = $connection->channel();

$channel->exchange_declare('direct_logs', 'direct', false, false, false);

$data = "(capacity=" . $capacity  . ",name=\"".$name."\",update_id=".$tuple_id.")";

$msg = new AMQPMessage($data);

$channel->basic_publish($msg, 'direct_logs', "create_lun");

$channel->close();
$connection->close();

$db->close();
?>
