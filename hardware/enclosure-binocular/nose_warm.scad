// Nose plate for the warm pod (camera 1, aims left, with the intake louvres).
// Print front face down with supports under the hood boss.
include <bino.scad>
translate([0, 0, body_l / 2 + nose_t]) rotate([-90, 0, 0]) nose(-1);
