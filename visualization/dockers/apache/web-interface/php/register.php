<?php

/*##############################################
# Hawkeye POC Portal                          #
# Author: Ankita Pawar (ankita.pawar@emc.com) #
###############################################*/

require_once(__DIR__ . '/include/util.inc');
require_once(__DIR__ . '/include/db_connect.php');

//header('Content-type: text/html');
header('Access-Control-Allow-Origin: *');

//print_r($_POST);

$db = new DB_Connect();
$db->connect();


    // Define $username and $password
    $username = string_escape(util_aiod($_POST, 'username', ""));
    $password = string_escape(util_aiod($_POST, 'password', ""));
    $email = string_escape(util_aiod($_POST, 'email', ""));


    $query = mysql_query("INSERT INTO `user` (name, email, password) values ('$username', '$email', '$password');");
    echo $query;
   
    $db->close();
?>

