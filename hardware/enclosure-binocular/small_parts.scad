// Plunger, plunger cap and two plugs (charge port and microSD). Print the plugs in TPU.
include <bino.scad>
translate([0, 0, 0]) rotate([0, -90, 0]) translate([-58.5, 0, 0]) plunger();
translate([30, 0, 0]) plunger_cap();
translate([0, 30, 0]) plug(charge_w, charge_h);
translate([0, 55, 0]) plug(sd_w, sd_h);
