// Corner camera enclosure, concept B: binocular.
// Shared parameters and modules. The part files include this one; it draws nothing itself.
//
// Axes: X across the rig (warm pod at -X, cool pod at +X), Y forward (+Y faces the pitch),
// Z up. Origin at the centre of the body on the lid split line.
// Every size is a variable. Values marked MEASURE are placeholders until the parts are on the bench.

$fn = 48;
eps = 0.01;

// ---------- Placeholders: MEASURE before printing ----------
board_w = 100;                // ROCK 5B+ width (X)
board_d = 72;                 // ROCK 5B+ depth (Y)
board_t = 1.6;
board_holes = [[-46.5, -32.5], [46.5, -32.5], [-46.5, 32.5], [46.5, 32.5]]; // from board centre
heatsink_h = 25;              // Radxa 6240B incl. fan, above the board
bank_w = 73;                  // Cygnett Encore 10000, across (X)
bank_l = 86;                  // along (Y)
bank_h = 30;
bank_button_y = 0;            // bank power button, along the bank from its centre (+ = forward)
bank_port_y = -30;            // bank USB-C port, same
sd_y = -40;                   // microSD slot on the board underside, world Y
cam_board = 38;               // Radxa Camera 4K board, square
cam_holes = 30;               // its M2 hole spacing, square
cam_holder_w = 20;            // M12 lens holder footprint, square
cam_standoff = 6;             // gap between pad and camera board
lens_r = 7;                   // radius of the 6mm lens front element
lens_barrel_d = 14;           // M12 barrel
lens_front = 2;               // lens front glass ahead of the nose plate face, along the lens axis

// ---------- Body ----------
pod_a = 56;                   // pod half-width (outer)
pod_b = 38;                   // pod half-height (outer)
pod_cx = 58;                  // pod centre offset from the middle
body_l = 136;                 // body length front to back
wall = 3;
bridge_w = 14;                // solid bridge between the pods
valley_z = 25;                // height of the valley floor (bridge top)
groove_w = 6;                 // rain channel in the valley floor
groove_d = 3;
spout_l = 12;                 // spout that carries the channel past the back wall

flange_w = 9;                 // internal flange at the lid split
flange_h = 6;                 // flange height on each half
gasket_g0 = 1;                // gasket groove: inner edge from the wall
gasket_g1 = 3.2;              // gasket groove: outer edge from the wall
gasket_d = 1.5;
lid_screws = [[-46.5, -50], [46.5, -50], [-46.5, 45], [46.5, 45]]; // per pod

ring_w = 7;                   // internal ring at the pod front for the nose plate
ring_t = 6;
nose_t = 4;

// ---------- Cameras and hoods ----------
lens_z = 2;                   // lens centre height on the nose plate
cam_splay = 15;               // each camera, away from the diagonal
cam_pitch = 19;               // down, relative to the body
body_tilt = 4;                // body sits tail-down on the bracket: 19 - 4 = 15 deg down overall
hfov = 50;                    // 6mm lens on IMX415
vfov = 29;
hood_margin = 1.5;            // clearance outside the field of view
pad_back = 18;                // camera pad face behind the nose plate front face
boss_len = 14;                // hood boss, ahead of the nose plate face
boss_w = 54;
boss_h = 40;
hood_top = 22;                // hood length on top (the visor)
hood_bottom = 14;             // hood length underneath
hood_wall = 2;
hood_flange_t = 3;
hood_flange_w = 52;
hood_flange_h = 30;
hood_screw_x = 22;

// ---------- Inside ----------
board_z = -18;                // underside of the board
board_yc = -26;
standoff_d = 6;
m25_insert_d = 3.6;
bank_yc = -15;
bank_z0 = -26;                // underside of the bank
foam_t = 3;
plunger_z = -11;
plunger_d = 6;
plunger_bore = 6.4;
led_hole = 8;                 // 5mm LED panel holder
led_z = -22;
led_dy = 22;                  // LED, forward of the plunger
charge_w = 16;
charge_h = 10;
sd_w = 16;
sd_h = 6;
sd_z = -21;
m3_insert_d = 4.0;
m3_clear = 3.4;
m3_head = 6.5;
mount_x = 6;                  // tripod insert, offset towards the battery
tripod_insert_d = 8.7;        // 1/4"-20 heat-set insert
tripod_insert_depth = 13;
level_d = 15;                 // round bubble level on the warm pod
level_y = 40;

// ---------- Helpers ----------
function sq_pts(a, b, n = 96) = [for (i = [0:n - 1]) let(t = 360 * i / n, c = cos(t), s = sin(t))
    [a * sign(c) * sqrt(abs(c)), b * sign(s) * sqrt(abs(s))]];
module sq2d(a, b) polygon(sq_pts(a, b));

// Extrude a 2D shape in the XZ plane between y0 and y1.
module prism_y(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

function inner_half_w(z) = (pod_a - wall) * pow(max(0, 1 - pow(abs(z) / (pod_b - wall), 4)), 0.25);
function req_w(d) = 2 * (lens_r + d * tan(hfov / 2) + hood_margin);
function req_h(d) = 2 * (lens_r + d * tan(vfov / 2) + hood_margin);
function ring_pts() = let(k = sqrt(cos(45)), A = (pod_a - wall - ring_w / 2) * k, B = (pod_b - wall - ring_w / 2) * k)
    [[A, B], [-A, B], [A, -B], [-A, -B]];

module at_pod(s) translate([s * pod_cx, 0, 0]) children();    // s = -1 warm, +1 cool
module at_pods() for (s = [-1, 1]) at_pod(s) children();

// Fit checks, printed in the console.
echo(str("Board side clearance at its height: ", inner_half_w(board_z) - board_w / 2, " mm"));
echo(str("Cradle wall at the pocket floor: ", inner_half_w(bank_z0 - foam_t) - 0.6 - (bank_w / 2 + foam_t + 0.5), " mm"));
echo(str("Room above the heatsink: ", (pod_b - wall) - (board_z + board_t + heatsink_h), " mm"));
echo(str("Hood mouth inside: ", req_w(boss_len + hood_top - lens_front), " x ", req_h(boss_len + hood_top - lens_front), " mm"));

// ---------- Body ----------
module pod_outer() prism_y(-body_l / 2, body_l / 2) sq2d(pod_a, pod_b);
module pod_inner() prism_y(-body_l / 2 + wall, body_l / 2 + 1) sq2d(pod_a - wall, pod_b - wall);

module body_outer() {
    at_pods() pod_outer();
    translate([-bridge_w / 2, -body_l / 2, -30]) cube([bridge_w, body_l, valley_z + 30]);
    translate([mount_x - 22, -30, -pod_b]) cube([44, 60, 14]);   // tripod pad
}

module flange_strip(w) difference() {
    translate([-(pod_a - wall), -body_l / 2 + wall]) square([2 * (pod_a - wall), body_l - wall]);
    translate([-(pod_a - wall - w), -body_l / 2 + wall + w]) square([2 * (pod_a - wall - w), body_l]);
}

module flanges() translate([0, 0, -flange_h]) linear_extrude(2 * flange_h) flange_strip(flange_w);

module nose_ring() prism_y(body_l / 2 - ring_t, body_l / 2) difference() {
    sq2d(pod_a - wall + 0.5, pod_b - wall + 0.5);
    offset(delta = -ring_w) sq2d(pod_a - wall, pod_b - wall);
}

module lid_columns() for (p = lid_screws) translate([p[0], p[1], flange_h - eps]) cylinder(d = 9, h = pod_b);

module standoffs() for (h = board_holes)
    translate([h[0], board_yc + h[1], -pod_b]) cylinder(d = standoff_d, h = board_z + pod_b);

module plunger_boss() translate([44, bank_yc + bank_button_y, plunger_z]) rotate([0, 90, 0]) cylinder(d = 12, h = 14);

module exhaust_hood() {
    translate([-26, -body_l / 2 - 12, 28]) cube([52, 12 + eps, 2.5]);
    for (x = [-26, 24]) translate([x, -body_l / 2 - 12, 10]) cube([2, 12 + eps, 20.5]);
}

module level_boss() translate([0, level_y, 30]) cylinder(d = level_d + 6, h = pod_b + 1.5 - 30);

module spout() translate([-bridge_w / 2, -body_l / 2 - spout_l, valley_z - 6]) cube([bridge_w, spout_l + eps, 6]);

// ---------- Cuts ----------
module gasket_groove() translate([0, 0, -gasket_d]) linear_extrude(gasket_d + eps) difference() {
    translate([-(pod_a - wall - gasket_g0), -body_l / 2 + wall + gasket_g0]) square([2 * (pod_a - wall - gasket_g0), body_l]);
    translate([-(pod_a - wall - gasket_g1), -body_l / 2 + wall + gasket_g1]) square([2 * (pod_a - wall - gasket_g1), body_l]);
}

module screw_cuts() for (p = lid_screws) {
    translate([p[0], p[1], -flange_h - eps]) cylinder(d = m3_insert_d, h = flange_h + eps);   // base: insert
    translate([p[0], p[1], -eps]) cylinder(d = m3_clear, h = pod_b + 5);                       // lid: clearance
    translate([p[0], p[1], flange_h]) cylinder(d = m3_head, h = pod_b + 5);                    // lid: counterbore
}

module nose_inserts() for (p = ring_pts())
    translate([p[0], body_l / 2 + eps, p[1]]) rotate([90, 0, 0]) cylinder(d = m3_insert_d, h = ring_t + 0.5);

module standoff_holes() for (h = board_holes)
    translate([h[0], board_yc + h[1], board_z - 5]) cylinder(d = m25_insert_d, h = 5 + eps);

module exhaust_slots() for (z = [13, 17, 21, 25]) translate([-22, -body_l / 2 - 1, z]) cube([44, wall + 2, 2.5]);

module sd_slot() translate([-pod_a - 1, sd_y - sd_w / 2, sd_z - sd_h / 2]) cube([wall + 6, sd_w, sd_h]);

module plunger_hole() translate([30, bank_yc + bank_button_y, plunger_z]) rotate([0, 90, 0]) cylinder(d = plunger_bore, h = 40);

module charge_opening() translate([pod_a - wall - 3, bank_yc + bank_port_y - charge_w / 2, plunger_z - charge_h / 2])
    cube([wall + 6, charge_w, charge_h]);

module led_opening() translate([40, bank_yc + bank_button_y + led_dy, led_z]) rotate([0, 90, 0]) cylinder(d = led_hole, h = 20);

module level_pocket() translate([0, level_y, pod_b + 1.5 - 3]) cylinder(d = level_d + 0.4, h = 4);

module tunnel() translate([-12, 0, -16]) cube([24, 30, 12]);          // ribbon, USB-C and LED leads

module valley_groove() {
    translate([-groove_w / 2, -body_l / 2 - spout_l - eps, valley_z - groove_d]) cube([groove_w, body_l - 6 + spout_l, groove_d + eps]);
    translate([-bridge_w / 2 - 1, -body_l / 2 - spout_l + 3, valley_z - 6 - eps]) cube([bridge_w + 2, 1.5, 1.2]); // drip kerf
}

module tripod_hole() translate([mount_x, 0, -pod_b - eps]) cylinder(d = tripod_insert_d, h = tripod_insert_depth);

// ---------- Whole shell, before the split ----------
module shell() difference() {
    union() {
        difference() { body_outer(); at_pods() pod_inner(); }
        intersection() {
            union() {
                at_pods() { flanges(); nose_ring(); lid_columns(); }
                at_pod(-1) standoffs();
                at_pod(1) plunger_boss();
            }
            body_outer();
        }
        at_pod(-1) { exhaust_hood(); level_boss(); }
        spout();
    }
    at_pods() { gasket_groove(); screw_cuts(); nose_inserts(); }
    at_pod(-1) { standoff_holes(); exhaust_slots(); sd_slot(); level_pocket(); }
    at_pod(1) { plunger_hole(); charge_opening(); led_opening(); }
    tunnel();
    valley_groove();
    tripod_hole();
}

module base() intersection() { shell(); translate([-200, -200, -100]) cube([400, 400, 100]); }
module lid() intersection() { shell(); translate([-200, -200, 0]) cube([400, 400, 100]); }

// ---------- Nose plate, one per pod (pod-local coordinates) ----------
// s = -1 warm pod (camera aims to -X, has the intake), +1 cool pod.
module cam_frame(s) translate([0, body_l / 2 + nose_t, lens_z]) rotate([0, 0, -s * cam_splay]) rotate([-cam_pitch, 0, 0]) children();
module slab(y, w, h) translate([0, y, 0]) cube([w, 0.02, h], center = true);

module nose(s) difference() {
    union() {
        prism_y(body_l / 2, body_l / 2 + nose_t) sq2d(pod_a, pod_b);
        hull() {                                          // camera pad behind the plate
            translate([0, body_l / 2, lens_z]) cube([cam_board + 6, 0.02, cam_board + 6], center = true);
            cam_frame(s) slab(-pad_back, cam_board + 6, cam_board + 6);
        }
        cam_frame(s) for (x = [-1, 1], z = [-1, 1])     // camera standoffs
            translate([x * cam_holes / 2, -pad_back + eps, z * cam_holes / 2]) rotate([90, 0, 0]) cylinder(d = 5, h = cam_standoff);
        hull() {                                          // hood boss in front of the plate
            translate([0, body_l / 2 + nose_t - 0.02, lens_z]) cube([boss_w, 0.02, boss_h], center = true);
            cam_frame(s) slab(boss_len, boss_w, boss_h);
        }
    }
    cam_frame(s) {
        translate([0, -pad_back - cam_standoff - 1, 0]) cube([cam_holder_w + 1, 2 * (pad_back + cam_standoff - 5), cam_holder_w + 1], center = true);
        translate([0, -6, 0]) rotate([-90, 0, 0]) cylinder(d = lens_barrel_d + 1, h = lens_front + 6 + eps);
        hull() {                                          // opening that clears the field of view
            slab(lens_front, max(req_w(0), lens_barrel_d + 1), max(req_h(0), lens_barrel_d + 1));
            slab(boss_len + 1, req_w(boss_len + 1 - lens_front), req_h(boss_len + 1 - lens_front));
        }
        for (x = [-1, 1], z = [-1, 1])
            translate([x * cam_holes / 2, -pad_back - cam_standoff - eps, z * cam_holes / 2]) rotate([-90, 0, 0]) cylinder(d = 1.8, h = cam_standoff + 5);
        for (x = [-hood_screw_x, hood_screw_x])
            translate([x, boss_len + 1, 0]) rotate([90, 0, 0]) cylinder(d = m3_insert_d, h = 7);
    }
    for (p = ring_pts()) {
        translate([p[0], body_l / 2 - eps, p[1]]) rotate([-90, 0, 0]) cylinder(d = m3_clear, h = nose_t + 1);
        translate([p[0], body_l / 2 + nose_t - 1.7, p[1]]) rotate([-90, 0, 0]) cylinder(d1 = m3_clear, d2 = 6.8, h = 1.7 + eps);
    }
    if (s < 0) for (z = [-28.5, -25.3, -22.1])          // intake louvres, sloping down outwards
        translate([0, body_l / 2 + nose_t / 2, z]) rotate([-35, 0, 0]) cube([40, 8, 1.6], center = true);
}

// ---------- Hood (cam-frame coordinates) ----------
// It is the visor: the top runs 8mm further forward than the bottom, so rain off the top drips clear of the lens.
module hood() {
    d0 = boss_len - lens_front;
    d1 = boss_len + hood_top - lens_front;
    H = req_h(d1) + 2 * hood_wall;
    function ycut(z) = boss_len + hood_bottom + (z + H / 2) / H * (hood_top - hood_bottom);
    difference() {
        union() {
            intersection() {
                hull() {
                    slab(boss_len, req_w(d0) + 2 * hood_wall, req_h(d0) + 2 * hood_wall);
                    slab(boss_len + hood_top, req_w(d1) + 2 * hood_wall, req_h(d1) + 2 * hood_wall);
                }
                multmatrix([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
                    linear_extrude(200, center = true)
                        polygon([[boss_len - 5, -60], [ycut(-60), -60], [ycut(60), 60], [boss_len - 5, 60]]);
            }
            translate([0, boss_len + hood_flange_t / 2, 0]) cube([hood_flange_w, hood_flange_t, hood_flange_h], center = true);
        }
        hull() {
            slab(boss_len - 1, req_w(d0 - 1), req_h(d0 - 1));
            slab(boss_len + hood_top + 1, req_w(d1 + 1), req_h(d1 + 1));
        }
        for (x = [-hood_screw_x, hood_screw_x])
            translate([x, boss_len - eps, 0]) rotate([-90, 0, 0]) cylinder(d = m3_clear, h = hood_flange_t + 1);
        translate([0, boss_len + hood_top - 3, req_h(d1 - 3) / 2]) cube([req_w(d1) - 2, 1.5, 2], center = true); // drip kerf
    }
}

// ---------- Battery cradle (cool-pod coordinates) ----------
module cradle() {
    pocket_w = bank_w + 2 * foam_t + 1;
    pocket_l = bank_l + 2 * foam_t + 1;
    top = bank_z0 + 14;
    difference() {
        intersection() {
            prism_y(bank_yc - pocket_l / 2 - 3, bank_yc + pocket_l / 2 + 3) sq2d(pod_a - wall - 0.6, pod_b - wall - 0.6);
            translate([-100, -200, -100]) cube([200, 400, 100 + top]);
        }
        translate([-pocket_w / 2, bank_yc - pocket_l / 2, bank_z0 - foam_t]) cube([pocket_w, pocket_l, 50]);
        for (sx = [-1, 1]) translate([sx * (pocket_w / 2 + 1.6) - 1.5, bank_yc - 11, -50]) cube([3, 22, 60]);   // strap slots
        translate([-(pocket_w / 2 + 3.5), bank_yc - 11, -50]) cube([pocket_w + 7, 22, 50 + bank_z0 - foam_t - 2]); // strap channel
        translate([0, bank_yc - pocket_l / 2 - 4, top]) rotate([-90, 0, 0]) cylinder(d = 24, h = 8);            // finger notch
    }
}

// ---------- Small parts ----------
module plunger() {           // along +X, cool-pod coordinates
    x0 = bank_w / 2 + 0.5;   // tip, just off the bank's side
    difference() {
        union() {
            translate([x0, 0, 0]) rotate([0, 90, 0]) cylinder(d = plunger_d, h = 58.5 - x0);
            translate([42, 0, 0]) rotate([0, 90, 0]) cylinder(d = 10, h = 2);       // stop collar
        }
        translate([49.5, 0, 0]) rotate([0, 90, 0]) difference() {                 // O-ring groove
            cylinder(d = plunger_d + 1, h = 1.6);
            cylinder(d = plunger_d - 2, h = 1.6);
        }
    }
}
module plunger_cap() difference() { cylinder(d = 14, h = 6); translate([0, 0, 2]) cylinder(d = plunger_d + 0.2, h = 5); }

module plug(w, h) {          // TPU plug with a pull tab
    translate([-(w + 6) / 2, -(h + 6) / 2, 0]) cube([w + 6, h + 6, 1.6]);
    translate([-(w - 0.4) / 2, -(h - 0.4) / 2, 1.6 - eps]) cube([w - 0.4, h - 0.4, 4]);
    translate([(w + 6) / 2 - eps, -3, 0]) cube([8, 6, 1.6]);
}
