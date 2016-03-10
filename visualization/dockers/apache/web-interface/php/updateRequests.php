<?php
require_once(__DIR__ . '/include/util.inc');
require_once(__DIR__ . '/include/db_connect.php');

//header('Content-type: text/html');
header('Access-Control-Allow-Origin: *');

$db = new DB_Connect();
$db->connect();

$update_id = string_escape(util_aiod($_POST, "update_id", ""));
$status = string_escape(util_aiod($_POST, "status", ""));

$cmd = "UPDATE `requests` SET status='$status' WHERE ID =$update_id;";

echo "$update_id:$status";
echo $cmd;

$result = mysql_query($cmd);

$db->close();
?>
