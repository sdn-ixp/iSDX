function registerForm(oFormElement)
{
  var username = oFormElement.usernamesignup.value;
  var password = oFormElement.passwordsignup.value;
  var password_confirm = oFormElement.passwordsignup_confirm.value;
  var email = oFormElement.emailsignup.value;

  var params = "username=" + username + "&password=" + password + "&email=" + email;

  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("register_url");

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
            console.log("register-page: " + readCookie("username"));
            self.location="index.html";
          }
      }
  }
  //xmlhttp.send(new FormData(oFormElement));
  xmlhttp.send(params);
  document.getElementById("register_form").reset();
  return false;
}
