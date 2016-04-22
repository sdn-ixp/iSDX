# Notes on this data

This data was collected at 2.1 second intervals.  The original data
collection was at 1 second intervals, but the 1 second interval gave
odd results because (it appears) some of the switch stats are only
updated within the switch every 2 seconds.

The data consists of:
 * an initial flurry of BGP and ARP
 * a 20 second flow from A to B (140.0.0.1:80)
 * a 10 second idle period
 * a 20 second flow from A to C1 (140.0.0.1:4321)
 * a 10 second idle period
 * a 20 second flow from A to C2 (140.0.0.1:4322)

