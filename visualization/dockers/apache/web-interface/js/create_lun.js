function submitForm(oFormElement)
{
  var id = oFormElement.serial_list.value;
  var name = oFormElement.name.value;
  var capacity = oFormElement.capacity.value;
  var sp = oFormElement.sp_type.value;
  var params = "ID=" + id + "&name=" + name + "&capacity=" + capacity + "&sp=" + sp + "";

  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("create_lun_url");

  xmlhttp.open("POST", url, true);
  xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  xmlhttp.onreadystatechange=function()
  {
      if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
      {
          ;
      }
  }
  //xmlhttp.send(new FormData(oFormElement));
  xmlhttp.send(params);
  document.getElementById("create_lun_form").reset();
  return false;
}
