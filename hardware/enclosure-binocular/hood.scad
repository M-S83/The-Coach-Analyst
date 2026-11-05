// Lens hood. Print two, flange down. It is the visor: no separate visor is needed.
include <bino.scad>
translate([0, 0, -boss_len]) rotate([90, 0, 0]) hood();
