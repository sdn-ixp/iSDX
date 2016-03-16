<?php
require_once(__DIR__ . '/include/db_connect.php');
header('content-type: application/json; charset=utf-8');
header("access-control-allow-origin: *");

//ini_set('display_errors', 1);

$db = new DB_Connect();
$db->connect();

if ($_POST){
	extract($_POST);
}else { $serial='APM00143230622';}
  
$result = mysql_query("SELECT * FROM requests ORDER BY ID DESC");
$out = "[";

while($record = mysql_fetch_array($result))
{
	$sql_serial = mysql_query("SELECT serial_no FROM array where ID ='" . $record['system_id'] . "'");
	$row_serial = mysql_fetch_array($sql_serial);
	$serial = $row_serial['serial_no'];
	if ($out != "[") {$out .= ",";}
	$out .= '{"serial":"'  . $serial . '",';
	$out .= '"status":"' . $record['status'] . '",';
	$out .= '"type":"' . $record['type'] . '",';
	$out .= '"id":"' . $record['ID'] . '"}';
}
$out .= "]";

$db->close();

echo($out);
?>
