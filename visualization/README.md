There are currently three ways to visualize SDX traffic in real time.
All work by polling the OpenFlow port and flow counters.

 1. The original visualization mechanism is described further down
 under 'Basic SDX Visualization'.
 1. A web based version that is implemented using docker containers is
 described under the `dockers` directory.
 1. The latest version -- described below -- uses Grafana (very slick
   web interface) to 
   display flows.  It is generally better than the earlier versions,
   but does not show traffic overlaid on a network diagram (the
   earlier versions do).

# SDX Visualization with Grafana

The Grafana visualization works as follows:
 * A Ryu app called `gauge.py` periodically polls the switches for
   port and flow statistics.  The code for this is in `flanc/stats`.
   To enable this Ryu app, you must include the `--stats` argument
   when running phase 3 (which starts Ryu) of the `launch.sh` script.
   I.e.:

	`iSDX/launch.sh --stats test-ms 3`

   Configuration information for the gauge app is located alongside
   the `sdx_global.cfg` file.  The `gauge.conf` file contains one line
   per datapath (switch) with the name of a `.yaml` file that contains
   the configuration data for that switch.  *At the time of this
   writing, there is only gauge configuration data for `test-ms`.*

   Note that the gauge code was borrowed from
   https://github.com/REANNZ/faucet/tree/master/src/ryu_faucet/org/onfsdn/faucet.

 * The gauge app stores the data it collects in an InfluxDB database.
   It you want to see all the different time series that are stored in
   the DB, after iSDX has run -- i.e., after some data has been stored
   in the DB -- run:

	`influx -database sdx -execute 'show series'`

 * Grafana is a web application that for our purposes is configured to
   display data from this InfluxDB database.  To run Grafana, simply point
   your browser at `http://<iSDX_HOST>:3000`.  The login and password
   are both 'admin'.  Select the `iSDX` dashboard and set the time
   interval (upper right) to something like `last 15 minutes`.
   Grafana is currently configured to show several
   graphs.  You can easily change them or add other graphs.  If you
   save changes to the Grafana configuration, they are stored in
   Grafana's SQLite database, `/var/lib/grafana/grafana.db`.  You can
   dump the database with the command: `sqlite3
   /var/lib/grafana/grafana.db 'dump'`. If you want to commit this
   database to the SDX repo, save the output of the above command to
   `iSDX/setup/grafana-init.sql`.  This file is used to initialize the
   database when the vagrant machine is provisioned.

![Grafana SDX Screenshot]
(images/grafana.png)

# Basic SDX Visualization

The `gen_sdx_viz` script is a poor man's visualization tool.  It
monitors packet counts in the switches and generates a series of `.png`
files showing the network graph. These can be displayed as an animation of
packet flows.  For the most part, each edge shown in the graph
corresponds to a flow rule (or set of flow rules) that matched a
non-zero number of packets in the previous time interval.  (Interval
is currently hard coded as 1 second.)  In cases where a component,
such as a participant, sends to a switch, it is not possible in
general to determine from flow rule stats which edge to display, since
rules do not necessarily correspond to a particular input port.  In
these cases, the displayed edges correspond to non-zero packet counts
associated with the input port of the switch.  These edges associated
with input port packet counts are displayed in black.

To run:

 `./gen_sdx_viz test-ms.cfg test-ms.dot <out_dir> &`

The arguments are:

 * `test-ms.dot` is a graphviz .dot file that includes every possible
   edge in the flow graph.  Edges in the file are annotated with *tags*
   that determine how (or if) they should be displayed.  There may be
   multiple edges between two nodes, each corresponding to different
   flow rules.  This file is used as a template for generating graphs
   to display.
 * `test-ms.cfg` maps Open Flow cookies to tags and *display style*.
 * `<out_dir>` is a directory where the script stores its output.  If
   the directory does not exist, the script will create it.  If it
   does exist, the script will clean out (most of) the files in the directory.

The script does not actually display the graph.  To display the graph,
use a tool that displays .png files, such as `feh` (available via
apt-get).  There are several ways to display the graph:

To display almost in real time:

   `feh -R 1 <out_dir>/cur.png`

`gen_sdx_viz` updates `cur.png` once a second. The `-R 1` argument tells
feh to redisplay `cur.png` once a second.

The script stores all of the .png files it creates, so it is possible
to play them back later as a slideshow using the command:

   `feh [-D 1] <out_dir>/png`

If the `-D 1` argument is specified, the slideshow will play with 1
second between image reloads (or you can speed it up by specifying a
value smaller than 1, such as .5).  If the `-D 1` argument is not
specified, then you can advance the slideshow with a mouse or key
click.

## How it Works

After gen_sdx_viz collects packet counts from the switches, for each
cookie in each flow it calculates how many packets matched the flow
since the last collection.  Using that, together with the mapping of
cookies to tags from the .cfg files, it creates a count for each tag.
If a tag is associated with multiple cookies, the sum of their counts is
associated with the tag.  A style is associated with each tag.
(The set of styles is currently hardcoded in the script.)  If the
count for the tag is 0, then the style for the tag is 'invisible' -- i.e., the
corresponding edge is not displayed.  Otherwise, the tag is displayed
with the specified style.  For example, BGP-related flows are
currently displayed with the 'bgp' style with translates to
'color=red' and ARP-related flows are displayed with the 'arp' style
which translates to 'color=blue'.  Also, larger counts are displayed
with thicker lines.

Using the style information associated with each tag, the script then
generates a .dot file starting with the template .dot file and
substituting the style information for tag annotations in the
template.

Finally, the script uses the graphviz `dot` program to generate a .png
file from the .dot file.

### Customization

 * To change which style is associated with which tag, edit the .cfg file.
 * If switch port assignments change, just change the lines with
   'PORT' in them in the .cfg file. 
 * To change or add a style, you currently need to edit a hash (dictionary)
   in the script, but this is very straightforward.

## Notes

 * `gen_sdx_viz` leverages the scripts `of_show_flows` and
   `of_show_port_stats` which are in ~/iSDX/bin.  (The VM provisioning
   should have put this in your PATH.)  These scripts talk to the
   switch via the REST API of Ryu, so `ryu-manager` must be running
   with the REST API app. (Again, this should be set up to work by
   default.)  If the scripts cannot reach the switch, they currently
   fail silently.
 * Correct operation depends on a static assignment of cookie numbers
   to flow rules.  I.e., it depends on a particular cookie number
   corresponding to a particular rule; this is encoded in the .cfg
   file.  If cookie numbering becomes more dynamic, then the mapping
   of rules to tags will have to stop using cookie numbers and use
   some other mechanism, such as matching on the contents of the rule.
 * The display of images by feh is not synchronized with the creation of
   the .png file by gen_sdx_vis, so the display may sometimes either
   miss an image or display one twice.
 * Fetching of the flows from the switch is not atomic, so you may
   sometimes see graphs that look non-causal.  I.e., you might see a
   line representing a flow out of a switch while the corresponding
   flow into the switch does not appear until the next image.
 * Be careful not to have multiple instances of the script writing to
   the same directory at the same time.  Could give very confusing results.
