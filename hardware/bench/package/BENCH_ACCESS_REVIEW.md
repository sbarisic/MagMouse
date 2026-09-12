# Bench access and local return review

2026-09-12. This closes a source-geometry review, not physical fixture assembly.
No board holes, Hall locations or final-shell datums are changed.

- Main L1/C2 close-up: the switch exits directly from U2 to L1 on F.Cu;
  C1 and the exposed-pad ground exits stay local. C2 retains its ground stub
  and nearby via. The changed output connection remains wide. Saved In1 is
  continuous under the local signals. Native DRC and electrical regressions
  remain the quantitative acceptance checks.
- `package/thermal-return-inventory.csv` records ground pads and local vias
  for the regulator, eFuses, bridges, wheel driver, brake MOSFET/resistors and
  encoder. Every checked device ground pad reaches saved In1. Via counts alone
  are not thermal acceptance: U13 has one GND via within 3 mm and Q5 has none
  within that radius, so their connected copper spreading and measured heating
  must be evaluated during limited-current operation. No current limit is raised.
- `package/probe-access.csv` enumerates test pads by side and coordinates, with
  nearby ground test points and a 0.5 mm probe-tip screening envelope. Wheel
  **TP34 is obstructed by C90**; use the accessible J11 pin 1 for ACT_5V and
  pin 2 for its return with a secured, insulated test lead. Do not reach beneath
  C90 with a loose powered probe. Bottom test pads require tilting/removing the
  carrier. Prefer a short local ground spring for switching measurements;
  the nearest named ground pad is not automatically an adequate HF return.
- `support-clearances.csv` locates eight tab-adjacent saddles and two upright
  encoder clips in unit coordinates. It checks 5 mm saddle / 6 mm encoder-clip
  widths and 0.3 mm deep underside contact strips against
  exposed pads. Use nonconductive saddles and removable clamps; inspect top-side
  caps, mask, vias and real component envelopes before tightening.
- The motor/encoder carrier remains in the fixture's 100 x 100 mm area. Start
  with the projected encoder connector near base (150,60) mm, keep its cable
  route <=120 mm before slack/insertion allowance and use the selected 150 mm
  harness. The shorter historical 50 mm encoder lead is not the bench harness.
- Main-Wheel power uses 150 mm paired AWG22. J8/J9 use 150 mm AWG28 ribbon,
  fanned to the numbered solder lands. Fixture clamps grip insulation and
  leave slack at joints. There are no internal latches or FFC stiffeners.
  All 86 lands are also recorded as probe-access locations with nearby ground;
  a soldered wire may require approaching a land from below. USB/SPI probing
  uses compact existing lands, not added wire-loop test points.
- Button harnesses are 200 mm paired AWG24 leads to independent fixtures.
  Keep experimental coils/motor away from the fixed-magnet levers until interference
  is measured. No final actuator gap, paddle motion or motor bolt pattern is
  inferred from a provisional drawing.
- Set the optical slider from the confirmed lens drawing; the adjustable base
  height is not the optical working distance. Ploopy identity and physical lens
  retention remain open. Protect the aperture and keep the slider opening clear.

The generated connector pin views, copper close-ups and full panel/placement
views accompany this review. Planes and returns are checked electrically as
well as rendered; screenshots do not establish impedance or ADC accuracy.
Before combined effects, record local temperatures, rail droop, ADC noise,
brake response and wire/joint voltage drop with secured motor and magnets.
