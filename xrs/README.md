# xrs - SDX RS

This module is in charge of relaying BGP updates and announcements between the `exaBGP` 
and the `pctrlr` module respectively. It receives BGP updates from the `exaBGP` module and
forwards them to the `pctrlr`. It also receives announcements from the `pctrlr` which
it forwards to the `exaBGP` module.

See examples/test-ms/README.md for an example of how to run xrs along with everything else.
