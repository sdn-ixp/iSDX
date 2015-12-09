# Changes to manual merge branch.

The manual_merge branch manually merges the testing and master branch.
See 'git log' for details.
Changes so far:

## Cleanup of names and installation
This was a global change of sdx-ryu and sdx-parallel to iSDX.
Also, ryu-flags was chnged to include all of refmon.flowmodlog, refmon.input, and refmon.log.
Also, setup installs mongodb and pymongo in anticipation of its use.
Also, iSDX is *not* cloned, desiring to use the one mounted by vagrant. This will likely change for a non-vagrant (real) installation.

## Use mongo as an alternative to sqlite3
Testing uses mongo, but wholesale slam of the testing code into master gave me problems, so I decided to blend in mongo instead.
A problem is a different interface.
The db calls are wrapped in class rib.
They both offer the same routines, but master and testing behave a little differently.
In order to smoothly transition, they should both deliver the same kind of results.
Each rib would return whatever came out of the db.
For sqlite3, that is sqlite3.Row. For pymongo, it is a dict.
I introduced a namedtuple instead called RibTuple.
The sqlite3.Row allows addressing by int index or string index.
The dict just uses a string index.
The namedtuple allows addressing by int index or by attribute (with a '.', as in result.next_hop instead of result['next_hop']).
Now both return RibTuples, and the calling code has been changed to use attributes instead of string indexing.
This is discovered during runtime, since type errors in Python are discovered at runtime, so I may not have encountered all of the places that need to change yet.
But I grepped for all the db 'table' field names, so I think I got them all.
