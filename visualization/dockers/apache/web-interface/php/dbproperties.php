<?php
//
// Emit PCF mysql service connect info
//
require_once(__DIR__ . '/include/db_connect.php');
  print_r("host="   . DB_HOST . "\n");
  print_r("user="     . DB_USER . "\n");
  print_r("password="     . DB_PASSWORD . "\n");
  print_r("database=" . DB_DATABASE . "\n");
  print_r("port="     .DB_PORT );
?>
