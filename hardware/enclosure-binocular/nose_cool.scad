// Nose plate for the cool pod (camera 2, aims right). Print as the warm one.
include <bino.scad>
translate([0, 0, body_l / 2 + nose_t]) rotate([-90, 0, 0]) nose(1);
