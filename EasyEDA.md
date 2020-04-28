In the process of creating the PCBs for this project, I have created a couple of EasyEDA scripts that are quite useful. You can install scripts into EasyEDA using the Tools > Extensions > Load Scripts... option.

I recommend that you first download Duritskiy's [package of scripts](https://yadi.sk/d/MUeNNxXA4ULpLQ). You may find some of them useful, but in particular there is an Extension (still called "My Extension") that you can install (using Tools > Extensions > Extension Setting...) that adds an icon to the toolbar that lets you easily run any scripts you have loaded.

Available scripts in this repository are:

# [Relink](EasyEDA%20Scripts/relink.js)

A common task when creating the relay circuits is copy/pasting repeated track layouts. The problem is that the tracks and vias retain the original net names, and manually renaming them is tedious. What relink does is look for tracks and vias that have a blank net name and that have an endpoint that coincides with a object that has a net name; it then changes the net name of the track or via to match.

This means you can copy/paste a bunch of tracks, select them, change their net name to be blank (if all the selected objects have a net-name field, you'll be able to edit them using the info display on the left), lay down the new components on top of them (as needed) and then use Relink to fix their net names.

Relink will re-run itself up to 10 times to allow changes to propagate through the blank nets. In rare circumstances you may have to run it a second time.

Notes:

* As of this writing there is a bug in EasyEDA that sometimes sets net names to (null) when you copy/paste an object with a blank net name. Relink will not relink objects with null net names. However, you can fix this by selecting one of the offending objects, using Find Similar... to find other objects with the same null net name, and setting their net name back to blank. You will have to do this for tracks and vias separately.

* Relink only works with endpoints, so a track that passes through a pad without terminating at it will not be relinked.

# [Merge & Simplify](EasyEDA%20Scripts/merge.js)

When a PCB is edited a lot, often tracks will end up composed of a bunch of subtracks, and when you try and rearrange things, you have to rearrange each subtrack. Merge & Simplify will combine tracks with the same net name and a common endpoint. To keep things simple, on each invocation it will only do one combination per net name, so you will have to run it multiple times until it runs out of things to do.

The final time it runs, when it finds no more tracks to merge, it will do a simplify pass on each net, combining segments that share an endpoint and that have the same slope.

Notes:

* The simplify pass can cause two track segments that meet at a pad or hole to be combined into a single segment that passes **through** the pad/hole. This is not a problem for PCB design or fabrication, but can occasionally mean a little extra editing when adjusting the track because it is no longer pinned to the object; if you drag it around, it may slide off the object.
