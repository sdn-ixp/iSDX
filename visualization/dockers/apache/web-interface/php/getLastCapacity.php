<?php
require_once(__DIR__ . '/include/db_connect.php');
header('content-type: application/json; charset=utf-8');
header("access-control-allow-origin: *");

$db = new DB_Connect();
$db->connect();

if ($_POST){
	extract($_POST);
}else { $serial='APM00143230622';}

$result = mysql_query("SELECT DISTINCT(ts) ts, syscap, freecap, unconfigcap, usedcap FROM capacity_stat where serial='$serial' order by ts desc limit 1");
$out = "[";

while($record = mysql_fetch_array($result))
{
	if ($out != "[") {$out .= ",";}
	$out .= '{"ts":"'  . $record['ts'] . '",';
	$out .= '"usedcap":"' . $record['usedcap'] . '",';
  $out .= '"freecap":"' . $record['freecap'] . '",';
  $out .= '"unconfigcap":"' . $record['unconfigcap'] . '",';
	$out .= '"syscap":"' . $record['syscap'] . '"}';
}
$out .= "]";

$db->close();

echo($out);
?>
