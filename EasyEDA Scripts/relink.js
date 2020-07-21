// Relink objects with blank NET by finding a net they touch
//
// 2020-01-01 by MadOverlord, trebor@animeigo.com
//
// TRACK[gId, layerid, net, pointarr[].x,y]]
// PAD[gId, layerid, net, x, y]
// VIA[gId, layerid, net, x, y]
// FOOTPRINT(TRACK, PAD, VIA)
// layerId 11 = all
//
// json documentation: https://gist.github.com/dillonHe/071d4680dcdbf6bf9dd6
//
// This could be a lot faster, but I am prioritizing simplicity here
// because I don't program in Javascript regularly, and I want it to
// be very clear what the script is doing.
//
// Typical Use case:
//
// Copy/Paste the wiring for a module you want to duplicate.
// Select all the wires, holes and vias (turning off unneeded layers helps)
// Set net to blank.
// Move new components into position.
// Run script multiple times until it doesn't find any nets to update.
// Profit!

function relink(json, obj, owner) {

    var id, item, point, new_net, count=0;

    const TOLERANCE = 1;    // how close to dead center match we require; footprints often have tiny offsets

    function netAt(obj, x, y, layer) {

        var id, item, point, net, temp;

        for (id in obj.TRACK) {
            item = obj.TRACK[id];
            if (item.net != "" && item.net != "null" && item.net !== null && (item.layerid == layer || item.layerid == 11 || layer == 11)) {
                for (point of item.pointArr) {
                    if (Math.abs(point.x-x) < TOLERANCE && Math.abs(point.y-y) < TOLERANCE) {
                        return item.net;
                    }
                }
            }
        }

        for (id in obj.VIA) {
            item = obj.VIA[id];
            if (item.net != "" && item.net != "null" && item.net !== null && (item.layerid == layer || item.layerid == 11 || layer == 11)) {
                if (Math.abs(item.x-x) < TOLERANCE && Math.abs(item.y-y) < TOLERANCE) {
                    return item.net;
                }
            }
        }

        for (id in obj.PAD) {
            item = obj.PAD[id];
            if (item.net != "" && item.net != "null" && item.net !== null && (item.layerid == layer || item.layerid == 11 || layer == 11)) {
                if (Math.abs(item.x-x) < TOLERANCE && Math.abs(item.y-y) < TOLERANCE) {
                    return item.net;
                }
            }
        }

        // Footprint contains subelements, so we recurse

        for (id in obj.FOOTPRINT) {
            net = netAt(obj.FOOTPRINT[id], x, y, layer);
            if (net != "" && item.net != "null" && item.net !== null) {
                return net;
            }
        }

        // Fail - will return "" if null or "null"

        return ""

    }

    console.log("Tracks");

    for (id in obj.TRACK) {
        if(json.TRACK.hasOwnProperty(id)) {
            item = obj.TRACK[id];
            if (item.net == "" || item.net == "null" || item.net === null) {
                console.log("Attempting", id, item);
                for (point of item.pointArr) {
                    new_net = netAt(json, point.x, point.y, item.layerid);
                    if (new_net != "") {
                        api('updateShape', {
                                "shapeType": "TRACK",
                                "jsonCache": {
                                "gId": item.gId,
                                "net": new_net
                            }
                            });
                        console.log("Netted", new_net, item);
                        count += 1;
                        break;
                    }
                }
            }
        }
    }

    console.log("Vias");

    for (id in obj.VIA) {
        item = obj.VIA[id];
        if (item.net == "" || item.net == "null" || item.net === null) {
            console.log("Attempting", id, item);
            new_net = netAt(json, item.x, item.y, item.layerid);
            if (new_net != "") {
                api('updateShape', {
                        "shapeType": "VIA",
                        "jsonCache": {
                        "gId": item.gId,
                        "net": new_net
                    }
                    });
                console.log("Netted", new_net, item);
                count += 1;
            }
        }
    }

    console.log("Pads");

    for (id in obj.PAD) {
        item = obj.PAD[id];
        if (item.net == "" || item.net == "null" || item.net === null) {
            console.log("Attempting", id, item);
            new_net = netAt(json, item.x, item.y, item.layerid);
            if (new_net != "") {
                api('updateShape', {
                        "shapeType": "PAD",
                        "shape": item.shape,
                        "type": item.type,
                        "jsonCache": {
                        "gId": item.gId,
                        "net": new_net
                    }
                    });
                console.log("Netted", new_net, item);
                count += 1;
            }
        }
    }

    // Footprint contains subelements, so we recurse - disabled for now
    // because I don't know how to update subelements!

    // console.log("Footprints");
    //
    // for (id in obj.FOOTPRINT) {
    //  count += relink(json, obj.FOOTPRINT[id], id);
    // }

    return count;

}

var json, count=0, i=0;

// Do up to 10 passes of relinking.

do {
    json = api('getSource', {type: "json"});
    count = relink(json, json, null);
    i += 1;
    alert("Relink Pass " + i + ": " + count + " nets were updated.")
} while (count > 0 && i < 10);

if (count > 0) {
    alert("Relink v2: exited after 10 passes; run again.");
}
