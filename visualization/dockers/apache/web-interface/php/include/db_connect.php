<?php

// ------------------------------------------------
// csl:  Added for PCF MySQL connectivity
// ------------------------------------------------
$services = getenv('VCAP_SERVICES');
$json = json_decode($services, TRUE);
// Parse the json string that we got from VCAP_SERVICES

// Pivotal Mysql
$dbname = $json['p-mysql'][0]['credentials']['name'];
$hostname = $json['p-mysql'][0]['credentials']['hostname'];
$user = $json['p-mysql'][0]['credentials']['username'];
$password = $json['p-mysql'][0]['credentials']['password'];
$port = $json['p-mysql'][0]['credentials']['port'];

define('DB_HOST',"$hostname");
define('DB_USER',"$user");
define('DB_PASSWORD',"$password");
define('DB_DATABASE',"$dbname");
define('DB_PORT',"$port");
// ------------------------------------------------

class DB_Connect {

    // constructor
    function __construct() {

    }

    // destructor
    function __destruct() {
        // $this->close();
    }

    // Connecting to database
    public function connect() {
        // connecting to mysql
        $con = mysql_connect(DB_HOST, DB_USER, DB_PASSWORD);
        // selecting database
        mysql_select_db(DB_DATABASE);

        // return database handler
        return $con;
    }

    // Closing database connection
    public function close() {
        mysql_close();
    }

}

?>
