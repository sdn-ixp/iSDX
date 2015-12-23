# pctrl - Participants' SDX Controller

This module is in charge of running an `event handler` for each SDX participant. This `event handler`
receives network events from `xrs` module (BGP updates), `arproxy` module (ARP requests), and participants's
control interface (high-level policy changes). It processes incoming network events to generate new
BGP announcements and data plane updates. It sends the BGP announcements to the `xrs` module and
dp updates to the `flanc` module. 

See examples/test-ms/README.md for an example of how to run pctrl along with everything else.
