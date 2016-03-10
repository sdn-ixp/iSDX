var xmlhttp = new XMLHttpRequest();
var url = localStorage.getItem("serial_url");

xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
        myFunction(xmlhttp.responseText);
    }
}
xmlhttp.open("GET", url, true);
xmlhttp.send();

function myFunction(response) {
    var arr = JSON.parse(response);
    var i;
    var request_table = '';

    for(i = 0; i < arr.length; i++)
    {
      request_table += '<option value=\"' + arr[i].id + '\">' + arr[i].serial + '</option>';
    }
    document.getElementById('serial_list').innerHTML = request_table;
}
