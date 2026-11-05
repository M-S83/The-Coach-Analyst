// Whole rig for checking fit. Set explode > 0 to pull the parts apart.
include <bino.scad>
explode = 0;

color("#2A3036") base();
color("#F5C518") translate([0, 0, explode]) lid();
for (s = [-1, 1]) at_pod(s) {
    color("#15191D") translate([0, explode, 0]) nose(s);
    color("#15191D") translate([0, 2 * explode, 0]) cam_frame(s) hood();
}
at_pod(1) {
    color("#3D7DC8") translate([0, 0, -explode]) cradle();
    color("#B24A18") plunger();
    color("#FFFFFF", 0.6) translate([-bank_w / 2, bank_yc - bank_l / 2, bank_z0]) cube([bank_w, bank_l, bank_h]);
}
at_pod(-1) {
    color("#2F6B44") translate([-board_w / 2, board_yc - board_d / 2, board_z]) cube([board_w, board_d, board_t]);
    color("#B24A18", 0.7) translate([-40, board_yc - 30, board_z + board_t]) cube([80, 60, heatsink_h]);
}
