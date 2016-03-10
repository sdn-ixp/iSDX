<?php

/*##############################################
# Hawkeye POC Portal                          #
# Author: Ankita Pawar (ankita.pawar@emc.com) #
###############################################*/

function util_aiod($array, $index, $default)
{
  return array_key_exists($index, $array) ? $array[$index] : $default;
}

function string_escape($str = "")
{
  return addslashes($str);
}
?>

