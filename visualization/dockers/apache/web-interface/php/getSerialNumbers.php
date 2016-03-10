<?php
require_once(__DIR__ . '/include/db_connect.php');
header('content-type: application/json; charset=utf-8');
header("access-control-allow-origin: *");

$db = new DB_Connect();
$db->connect();

if ($_POST){
	extract($_POST);
}else { $serial='APM00143230622';}
  
$result = mysql_query("SELECT * FROM array");
$out = "[";

while($record = mysql_fetch_array($result))
{
	if ($out != "[") {$out .= ",";}
	$out .= '{"serial":"'  . $record['serial_no'] . '",';
	$out .= '"id":"' . $record['ID'] . '"}';
}
$out .= "]";

$db->close();

echo($out);
?>
