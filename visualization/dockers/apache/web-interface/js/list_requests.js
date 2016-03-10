function reload_request_list() {
  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("requests_url");

xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
        myFunction(xmlhttp.responseText);
    }
}
// xmlhttp.open("GET", url, true);
xmlhttp.open("GET", url, false);
xmlhttp.send();

function myFunction(response) {
    var arr = JSON.parse(response);
    var i;
    var request_table = '';
    request_table += '<tr>';
    request_table += '<th> No. </th>';
    request_table += '<th> Type</th>';
    request_table += '<th> Serial </th>';
    request_table += '<th> Status </th>';
    request_table += '</tr>';

    for(i = 0; i < arr.length; i++)
    {
      var status = "";

      if(arr[i].status == 'P')
      {
        status='two-gears-rotate' ;
      }
      else if(arr[i].status == 'C')
      {
        status='flag' ;
      }
      else if(arr[i].status == 'A')
      {
        status='eye' ;
      }
      else if(arr[i].status == 'N')
      {
        status='hamburger' ;
      }
      else if(arr[i].status == 'F')
      {
        status='attention' ;
      }
      var icount = i+1;
      request_table += '<tr>';
      request_table += '<td value=\"' + arr[i].id + '\">' + icount + '</td>';
      request_table += '<td value=\"' + arr[i].id + '\">' + arr[i].type + '</td>';
      request_table += '<td value=\"' + arr[i].id + '\">' + arr[i].serial + '</td>';
      request_table += '<td><div class=\"' + status + '\"></div></td>';
      request_table += '</tr>';

    }
    document.getElementById('request_table').innerHTML = request_table;
}
}
