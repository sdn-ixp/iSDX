<?php
/*##############################################
# Hawkeye POC Portal                          #
# Author: Ankita Pawar (ankita.pawar@emc.com) #
###############################################*/

require_once(__DIR__ . '/include/db_connect.php');

  print_r("DB_HOST="   . DB_HOST . "<br> ");
  print_r("DB_USER="     . DB_USER . "<br> ");
  print_r("DB_PASSWORD="     . DB_PASSWORD . "<br> ");
  print_r("DB_DATABASE=" . DB_DATABASE . "<br> ");
  print_r("DB_PORT="     .DB_PORT . "<br> <br>");

  $db = new DB_Connect();
  $db->connect();

  $sql = "create table user( ID int NOT NULL AUTO_INCREMENT, name text, email text, password text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table array( ID int NOT NULL AUTO_INCREMENT, name text, serial_no text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table requests( ID int NOT NULL AUTO_INCREMENT, system_id text, cmd text, type text, status text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table cpu_stat(ID int NOT NULL AUTO_INCREMENT, ts datetime, spa int, spb int, serial text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table iops_stat(ID int NOT NULL AUTO_INCREMENT, ts datetime, spa_read int, spa_write int, spb_read int, spb_write int, serial text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table capacity_stat(ID int NOT NULL AUTO_INCREMENT, ts datetime, syscap int, usedcap int, freecap int, unconfigcap int, serial text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  $sql = "create table healthcheck (ID int NOT NULL AUTO_INCREMENT, ts datetime, score int, serial text, note text, PRIMARY KEY (ID))";
  mysql_unbuffered_query($sql  );

  // Insert data in array table for poc
  $sql = "select * from array where serial_no = 'APM00143230622'";
  $query = mysql_query($sql);
  $rows = mysql_num_rows($query);
  print_r("Array Rows for APM00143230622: " . $rows);

  if ( $rows < 1 ) {
    $sql = mysql_query("INSERT INTO `user` (name, email, password) values ('imetools', 'imetools@emc.com','imetoolspw');");
    mysql_query($sql);

    $sql = mysql_query("INSERT INTO `array` (name, serial_no) values ('POC Array', 'APM00143230622');");
    mysql_query($sql);

    $sql = mysql_query("INSERT INTO `cpu_stat` (ts, spa, spb, serial) values ('07/04/2015 10:03:13',75,80,'APM00143230622');");
    mysql_query($sql);

    $sql = mysql_query("INSERT INTO `iops_stat` (ts, spa_read, spa_write, spb_read, spb_write, serial) values ('07/04/2015 10:03:13',222,244,,281,291,'APM00143230622');");
    mysql_query($sql);

    $sql = mysql_query("INSERT INTO `requests` (system_id,cmd,type,status) values ('APM00143230622','naviseccli lun -create -type  Thin -capacity 256 -sq gb -poolId 0 -sp A  -aa 1 -name LUN 20150710 -offset 0 -tieringPolicy autoTier -initialTier highestAvailable','create_lun','N');");
    mysql_query($sql);
  }



  print_r("Database Initialized");


  //$result = mysql_query("show tables");
  //var_dump($result);

  $DB->db_close();

?>
