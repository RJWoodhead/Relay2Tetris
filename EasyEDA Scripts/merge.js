// Merge tracks with coincident endpoints that are in the same net, layer and have same stroke width.
// Simplify tracks that have adjacent line segments with the same slope.
//
// 2020-06-20 by MadOverlord, trebor@animeigo.com
//
// json documentation: https://gist.github.com/dillonHe/071d4680dcdbf6bf9dd6
//
// Things I learned: correct way to update a track is to delete it and recreate it.
//
// Made slightly smarter, so that if there is a large group of tracks with same net/size, if it finds
// two that can be merged, it does so and removes the pair from the list, and then repeats. So it
// can grind through complex multisegment tracks (like GND) in fewer invocations.

const DEBUG = true;

// Are two points the same (within some tolerance)?

const TOLERANCE = 0.1;

function coincident(a, b) {

    return (Math.abs(a.x - b.x) <= TOLERANCE) && (Math.abs(a.y - b.y) <= TOLERANCE);

}

// Slope between two points. Javascript makes it easy.

function slope(a, b) {

    return (a.x - b.x) / (a.y - b.y);

}

// Are slopes same between point triplet? This works with Infinities!

function inline(a, b, c) {

    var s1, s2;

    s1 = slope(a, b);
    s2 = slope(b, c);

    if (s1 == s2) return true;

    return Math.abs(s1-s2) < TOLERANCE;

}

// Simplify the current tracks

function simplify(json) {

    var count=0, item, points, original_length, i;

    if (DEBUG) console.log("Simplifying tracks ", json.TRACK);

    for (var id in json.TRACK) {
        item = json.TRACK[id];
        if (DEBUG) console.log("Testing", id, item);
        if(json.TRACK.hasOwnProperty(id)) {
            if (item.net != "") {
                // Run through the track and see if there are any internal reductions that can be made; if
                // so, update the track

                points = item.pointArr;

                if (points.length > 2) {
                    if (DEBUG) {
                        console.log("Testing Array of length", points.length);
                        for (i = 0; i < points.length; i++) {
                            if (i != points.length - 1) {
                                console.log(i, points[i].x, points[i].y, slope(points[i], points[i+1]));
                            } else {
                                console.log(i, points[i].x, points[i].y);
                            }
                        }
                    }
                    original_length = points.length;
                    for (i = points.length - 2; i > 0; i--) {
                        if (coincident(points[i], points[i+1]) || inline(points[i-1], points[i], points[i+1])) {
                            points.splice(i, 1);
                        }
                    }

                    if (points.length != original_length) {
                        if (DEBUG) {
                            console.log("Simplified to", points.length);
                            for (i = 0; i < points.length; i++) {
                                console.log(i, points[i].x, points[i].y);
                            }
                        }
                        if (DEBUG) console.log("Deleting", item.gId);
                        api('delete', {ids:[item.gId]});
                        if (DEBUG) console.log("Recreating", item.gId);
                        api('createShape', {
                          "shapeType": "TRACK",
                          "jsonCache": {
                            "gId": item.gId,
                            "layerid": item.layerid,
                            "net": item.net,
                            "pointArr": points,
                            "strokeWidth":item.strokeWidth
                          }
                        });
                        if (DEBUG) console.log("Recreated", item.gId);
                        count += 1;
                        if (count == 200) return count;
                    }
                }
            }
        }
    }

    return count;

}

// Merge conjoint tracks

function merge(json) {

    var tracks={}, count=0, id, item, key, group, i, j, g, glen, t1, t2, p1, p2;

    // Make dictionary of tracks organized by net-layer-width

    if (DEBUG) console.log("Merging tracks ", json.TRACK);

    for (id in json.TRACK) {
        if (json.TRACK.hasOwnProperty(id)) {
            item = json.TRACK[id];
            if (item.net != "") {
                key = item.net + " " + item.layerid + " " + item.strokeWidth;
                if (!(key in tracks)) {
                    tracks[key] = [];
                }
                tracks[key].push(id);
            }
        }
    }

    if (DEBUG) console.log("Tracks groups before filter:", tracks);

    // Look for conjoint tracks.  Tracks are conjoint if the start/end of a track matches the start/end of
    // the other track. For simplicity, we only do one modification per group per pass. The modifications
    // are: if a tail matches a head, merge the two tracks. If two heads or two tails match, flip then
    // merge.

    progress = true;

    while (progress) {

        if (DEBUG) console.log("Main loop: # of tracks = ", tracks.length);

        progress = false;

        grouploop:

        for (g in tracks) {
            group = tracks[g];
            glen = group.length;
            if (glen > 1) {
                if (DEBUG) console.log("Testing tracks: ", g, group);
                for (i = 0; i < glen; i++) {
                    for (j = 0; j < glen; j++) {
                        if (i != j) {
                            if (DEBUG) console.log("Comparing ", group[i], group[j]);
                            t1 = json.TRACK[group[i]];
                            t2 = json.TRACK[group[j]];
                            p1 = t1.pointArr;
                            p2 = t2.pointArr;
                            if (DEBUG) console.log("p1 = ", p1);
                            if (DEBUG) console.log("p2 = ", p2);

                            if (coincident(p1[0], p2[0])) {
                                // Head-Head match
                                if (DEBUG) console.log("Head-Head match; reversing p1");
                                p1.reverse();
                                if (DEBUG) console.log("p1 = ", p1);
                            } else if (coincident(p1[p1.length-1], p2[p2.length-1])) {
                                // Tail-Tail match
                                if (DEBUG) console.log("Tail-Tail match; reversing p2");
                                p2.reverse();
                                if (DEBUG) console.log("p2 = ", p2);
                            }
                            if (coincident(p1[p1.length-1], p2[0])) {
                                if (DEBUG) console.log("Tail-Head match; combining");
                                p1 = p1.concat(p2.slice(1));
                                if (DEBUG) console.log("gId = ", t1.gId, "p1 = ", p1);
                                api('delete', {ids:[t1.gId]});
                                api('delete', {ids:[t2.gId]});
                                api('createShape', {
                                  "shapeType": "TRACK",
                                  "jsonCache": {
                                    "gId": t1.gId,
                                    "layerid": t1.layerid,
                                    "net": t1.net,
                                    "pointArr": p1,
                                    "strokeWidth": t1.strokeWidth
                                  }
                                });
                                count += 1;
                                if (count == 200) return count;

                                progress = true;

                                // remove the two tracks from the group.

                                if (j < i) {
                                    [i, j] = [j, i];
                                }
                                group.splice(i, 1);
                                group.splice(j-1, 1);
                                continue grouploop;
                            }
                        }
                    }
                }
            }
        }
    }

    return count;

}

var json, mc, sc;

json = api('getSource', {type: "json"});

mc = merge(json);
if (mc > 0) {
    alert("Merge: " + mc + " tracks merged.");
} else {
    sc = simplify(json);
    if (sc > 0) {
        alert("Merge: " + sc + " tracks simplified.");
    } else {
        alert("Merge: Nothing to merge or simplify.");
    }
}
