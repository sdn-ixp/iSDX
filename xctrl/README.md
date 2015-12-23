# xctrl - SDX Controller

This controller is in charge of pushing all the flow rules to the SDX fabric that are necessary to get the SDX running.

A sample config file (xctrl.cfg) is provided. In the config file the vmac mode and fabric setup has to be specified:

* vmac mode - at the moment only superset mode is supported "Superset"

* fabric setup - either "Multi-Switch" or "Multi-Table"

See examples/test-ms/README.md for an example of how to run xctrl along with everything else.
