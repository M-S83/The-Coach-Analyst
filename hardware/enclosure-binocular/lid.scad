// Lid: upper half of both pods with the rain valley. Print in yellow ASA, flange face down on the bed.
// Supports from the bed only under the valley spout and the exhaust hood.
include <bino.scad>
translate([0, 0, pod_b + 1.5]) rotate([180, 0, 0]) lid();
