function loginForm(oFormElement)
{
  var username = oFormElement.username.value;
  var password = oFormElement.password.value;
  var params = "username=" + username + "&password=" + password + "";

  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("login_url");
  console.log("url: " + url);
  xmlhttp.open("POST", url, true);
  xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  xmlhttp.onreadystatechange=function()
  {
      if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
      {
        console.log("Response: " + xmlhttp.responseText);
          if(xmlhttp.responseText > 0)
          {
            console.log("Response: " + xmlhttp.responseText);
            createCookie("username",username,1);
            console.log("profile-page: " + readCookie("username"));
            self.location="profile.html";
          }
      }
  }
  //xmlhttp.send(new FormData(oFormElement));
  xmlhttp.send(params);
  document.getElementById("login_form").reset();
  return false;
}

function createCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
}


function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name,"",-1);
}
