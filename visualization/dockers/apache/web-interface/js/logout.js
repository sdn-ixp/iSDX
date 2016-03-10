
function logout()
{
  eraseCookie("username");
  self.location="index.html";
  console.log("Logout JS:" + readCookie("username"));
}
