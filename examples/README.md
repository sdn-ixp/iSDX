# iSDX - Examples

The sub-directories here correspond to the three switch modes of iSDX:
* `test-mt` - are examples using the *multi-table* configuration.  These can
  be used on switches that support multiple tables, such as Open
  vSwitch which is used by Mininet.
* `test-ms` - are examples using the *multi-switch* configuration.  When
  switches don't support multiple tables, the effect of multiple
  tables can be achieved by using multiple switches.
* `test-os` - are examples using the *one-switch-with-loopbacks*
  configuration.  This is like the multi-switch configuration, but
  rather than using multiple switches, it uses a single switch with some of
  the output ports looped back to input ports so that packets can
  make multiple passes through the same switch.

