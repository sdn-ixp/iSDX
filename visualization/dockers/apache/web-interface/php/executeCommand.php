<?php
require_once(__DIR__ . '/include/db_connect.php');
header('content-type: application/json; charset=utf-8');
header("access-control-allow-origin: *");

if ($_POST){
	extract($_POST);
}else { $serial='APM00143230622';}

exec('ls 2>&1', $output);
print_r($output);  // to see the respond to your command

?>
