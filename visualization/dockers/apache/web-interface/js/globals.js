function onLoadPage() {

// var nodejs_url = "http://127.0.0.1:3000";
// var apache_url = "http://10.245.12.198";

// ---------------------------------------
//   Read websocket info from stats-feed microservice
// ---------------------------------------
localStorage.setItem("nodejs", "http://192.168.99.100:8080");

// -------------------------------------

var apache_url = "http://192.168.99.100";

var cpu_uri = "getCPUHistory.php";
var serial_uri = "getSerialNumbers.php";
var requests_uri = "getRequestsStatus.php";
var login_uri = "login.php";
var register_uri = "register.php";
var create_lun_uri = "createLUNs.php";
var healthcheck_uri = "getLastHealth.php";
var capacity_uri = "getLastCapacity.php";
var execute_uri = "executeCommand.php";
console.log("globs");
// localStorage.setItem("nodejs", nodejs_url);
localStorage.setItem("execute_url", apache_url + "/php/" + execute_uri);
localStorage.setItem("cpu_url", apache_url + "/php/" + cpu_uri);

localStorage.setItem("serial_url", apache_url + "/php/" + serial_uri);
localStorage.setItem("requests_url", apache_url + "/php/" + requests_uri);
localStorage.setItem("register_url", apache_url + "/php/" + register_uri);
localStorage.setItem("login_url", apache_url + "/php/" + login_uri);
localStorage.setItem("create_lun_url", apache_url + "/php/" + create_lun_uri);
localStorage.setItem("healthcheck_url", apache_url + "/php/" + healthcheck_uri);
localStorage.setItem("capacity_url", apache_url + "/php/" + capacity_uri);
}
