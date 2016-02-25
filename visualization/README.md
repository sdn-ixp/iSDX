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
