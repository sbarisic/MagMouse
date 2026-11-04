# 1206 passive components

All 114 formerly 0603 resistors and 79 formerly 0603/0805 ceramic capacitors
use 1206 (3216 metric) footprints. Board dimensions, circuit values and wire
assignments are retained. The four 2512 brake resistors, polymer capacitor and
Bourns power inductor retain their existing packages.

Package bodies are nominally 3.2 x 1.6 mm. Capacitors use standard KiCad lands
1.15 x 1.8 mm; resistors use 1.125 x 1.75 mm lands. These are reflow footprints
suitable for solder paste and hot air. Component courtyards are checked.
Several crowded passive and connector ground pads use explicit traces into
the ground pour where automatic thermal spokes would not fit.

## Purchasing substitutions

| Circuit value | Replacement MPN | Rating | Quantity |
| --- | --- | --- | ---: |
| 0R | [RC1206JR-070RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | Jumper, 2 A | 6 |
| 100R | [RC1206FR-07100RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 1 |
| 100k | [RC1206FR-07100KL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 36 |
| 100nF | [CC1206KRX7R9BB104](https://www.yageogroup.com/download/specsheet/CC1206KRX7R9BB104) | 50 V, X7R, 10% | 33 |
| 10k | [RC1206FR-0710KL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 34 |
| 10nF | [CC1206KRX7R9BB103](https://www.yageogroup.com/download/specsheet/CC1206KRX7R9BB103) | 50 V, X7R, 10% | 3 |
| 10uF/25V | [CL31A106KAHNNNE](https://product.samsungsem.com/mlcc/CL31A106KAHNNN.do) | 25 V, X5R, 10% | 18 |
| 1M | [RC1206FR-071ML](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 3 |
| 1k | [RC1206FR-071KL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 5 |
| 1nF/50V | [CC1206KRX7R9BB102](https://www.yageogroup.com/download/specsheet/CC1206KRX7R9BB102) | 50 V, X7R, 10% | 1 |
| 1uF/50V | [CL31B105KBHNNNE](https://product.samsungsem.com/mlcc/CL31B105KBHNNN.do) | 50 V, X7R, 10% | 14 |
| 2.2uF/10V | [CL31B225KAHNNNE](https://product.samsungsem.com/mlcc/CL31B225KAHNNN.do) | 25 V, X7R, 10% | 3 |
| 22.1k | [RC1206FR-0722K1L](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 4 |
| 22R | [RC1206FR-0722RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 1 |
| 22pF/50V | [CC1206JRNPO9BN220](https://www.yageogroup.com/download/specsheet/CC1206JRNPO9BN220) | 50 V, C0G/NP0, 5% | 4 |
| 22uF/25V | [CL31A226KAHNNNE](https://product.samsungsem.com/mlcc/CL31A226KAHNNN.do) | 25 V, X5R, 10% | 1 |
| 3.3k | [RC1206FR-073K3L](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 5 |
| 330R | [RC1206FR-07330RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 4 |
| 33R | [RC1206FR-0733RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 3 |
| 33k | [RC1206FR-0733KL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 5 |
| 34.8k | [RC1206FR-0734K8L](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 1 |
| 39R | [RC1206FR-0739RL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 1 |
| 4.7k | [RC1206FR-074K7L](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 4 |
| 4.7uF/10V | [CL31A475KAHNNNE](https://product.samsungsem.com/mlcc/CL31A475KAHNNN.do) | 25 V, X5R, 10% | 1 |
| 47nF/50V | [CC1206KRX7R9BB473](https://www.yageogroup.com/download/specsheet/CC1206KRX7R9BB473) | 50 V, X7R, 10% | 1 |
| 887k | [RC1206FR-07887KL](https://pccomponents.com/datasheets/yageo-rc.pdf) | 0.25 W, 1% | 1 |

The capacitance labels in the schematics keep their circuit minimum voltage
ratings. The new 2.2 uF and 4.7 uF parts are rated for 25 V, above the original
10 V requirement. The 22 pF parts remain C0G/NP0 with 5% tolerance. The new
22 uF capacitor has 10% tolerance, compared with the previous 20%.

Manufacturer part numbers and ratings are selected from the linked manufacturer
product data. Supplier stock and JLCPCB assembly availability have not been
checked for this revision. Old LCSC numbers and product URLs are cleared so
a purchase does not accidentally select the smaller package.

The saved standard-via JLCPCB quote is historical evidence for revision 1392522.
It has not been refreshed for these regenerated Gerbers or for assembly of the
new 1206 BOM. The panel dimensions and standard via-drill tier remain the same.
