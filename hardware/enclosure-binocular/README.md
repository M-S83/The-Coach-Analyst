# Corner camera enclosure: binocular concept

OpenSCAD model of concept B: two rounded pods, one per camera, joined by a bridge whose top is a rain channel. The warm pod (−X) holds the ROCK 5B+ and camera 1. The cool pod (+X) holds the Cygnett bank and camera 2.

All sizes live in `bino.scad`. Every other file includes it and draws one printable part, already turned to its print orientation.

| File | Part | Print |
|---|---|---|
| `base.scad` | Lower half of both pods, board standoffs, plunger guide, tripod pad | Black ASA, flange face up, supports under the curved underside |
| `lid.scad` | Upper half of both pods, rain channel and spout, exhaust vent, bubble-level seat | Yellow ASA, flange face down; supports only under the spout and vent hood |
| `nose_warm.scad` | Front plate for the warm pod: camera pad at 15° splay and 19° down, intake louvres | Black ASA, front face down, supports under the hood boss |
| `nose_cool.scad` | Front plate for the cool pod | As above |
| `hood.scad` | Lens hood, print two | Black ASA, flange down |
| `cradle.scad` | Battery cradle, shaped to the pod floor | Any colour |
| `small_parts.scad` | Plunger, plunger cap, charge-port plug, microSD plug | Plugs in TPU |
| `assembly.scad` | Everything in place, for checking fit (`explode = 60` pulls it apart) | Not for printing |

Export with `openscad -o base.stl base.scad`, and the same for each part. When you open a part, the console prints four fit checks: board side clearance, cradle wall thickness, room above the heatsink and hood mouth size.

## Does it need a visor?

No separate visor. The hoods are the visors.

- **Rain from above:** the body sits 4° tail-down, so rain on the pods runs backwards and never over the front. Rain that lands on a hood runs forward along its top. The top extends 8mm further forward than the bottom, so it drips clear of the opening. A small groove under the top lip stops drips creeping back inside onto the glass.
- **Field of view:** each hood flares to stay just outside the 6mm lens's 50° × 29° view, with 1.5mm margin. A round hood that size would cut off the corners of the image.
- **Bench testing:** take the hoods off when using the stock 2.95mm lens. Its 75° view is wider than the hood.

## Bought parts

- 8 × M3 lid screws (4 per pod) with M3 heat-set inserts in the base flange
- 8 × M3 countersunk screws for the nose plates, with inserts in the pod front rings
- 4 × M3 for the hoods, with inserts in the hood bosses
- 8 × M2.5 heat-set inserts and screws for the board; M2 screws for the camera boards
- 2mm gasket cord for the lid groove; thin EVA foam gasket for each nose plate
- 1/4"-20 heat-set insert for the tripod pad
- 5mm LED panel holder, 330 Ω resistor, Dupont leads
- 4 × 1.5mm O-ring for the plunger, plus a light spring (a ballpoint pen spring works)
- Velcro strap (20mm) and EVA foam for the cradle
- Round bubble level, 15mm
- Stainless mesh behind the intake louvres and the exhaust slots

The spec lists a waterproof panel push-button. A panel switch switches electrically and can't push the bank's button. So this model uses a printed plunger through a sealed guide, with an O-ring and a cap on the outside.

## Measure before printing

These values in `bino.scad` are placeholders:

- **Board:** size, mounting holes and the microSD slot position (`board_w`, `board_d`, `board_holes`, `sd_y`, `sd_z`)
- **Heatsink:** height with the fan fitted (`heatsink_h`)
- **Bank:** size, plus where its button and USB-C port sit (`bank_w`, `bank_l`, `bank_h`, `bank_button_y`, `bank_port_y`)
- **Camera board:** size, hole spacing and lens holder footprint (`cam_board`, `cam_holes`, `cam_holder_w`)
- **Lens:** front element radius, barrel, and how far the glass sits ahead of the nose plate once focused (`lens_r`, `lens_barrel_d`, `lens_front`)
- **Ribbons:** camera 2's ribbon crosses to the board through the tunnel under the channel. It needs about 15cm.

## Fit at the placeholder sizes

- **Board:** 2mm clear of the curved walls at each side, sitting on 10mm standoffs.
- **Room above the heatsink:** 26mm.
- **Cradle:** walls 4.6mm thick at the pocket floor.
- **Battery:** sits 4mm above the lid split, with about 30mm free above it.
- **Size:** 228 × 136 × 77.5mm including the bubble-level seat. The hoods reach about 36mm ahead of the nose plates.
