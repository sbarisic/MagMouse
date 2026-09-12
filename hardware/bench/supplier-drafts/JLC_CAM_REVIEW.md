# DRAFT — not sent

Subject: Pre-order CAM and stencil review — three-design Rev-A bench panel

Please review the attached files before fabrication approval. We request no
order placement or payment. If formal CAM review requires an order, please
explain that requirement; we have not authorised ordering for this review.

Quantity is five bare 151 x 139 mm panels, with **three different designs** per
panel, plus one 220 x 200 mm unframed 0.10 mm stainless stencil. We will cut
the bare boards while supported, then stencil/reflow individual boards.

Confirm JLC041611-2116, nominal 1.6 mm, FR4 TG155, four layers, 1 oz inner and
outer copper, green mask, white silkscreen and ENIG 1 microinch. This is the
economy variant without paid impedance guarantee/testing; do not substitute
the stack. Main USB geometry is 0.1466 mm width / 0.1501 mm gap over In1 GND.
The exact construction and file-layer mapping are in STACK_AND_LAYERS.md.
Gerber-job impedance control is false for this economy order; the retained
90 ohm design target does not request paid impedance testing.
Enable production-file confirmation. Do not accept X-outs in these five panels.

Please confirm 2 mm routed board separation, ten 5 mm tabs with five 0.6 mm
holes per tab at 0.9 mm pitch, router access and adequate handling support.
Confirm the existing 0.20 mm minimum via drill / 0.45 mm pad without changing
the holes. All entries in all-vias.csv require epoxy filling and copper capping.
Do not fill component, mechanical, tooling or tab-perforation holes.
Fill 1,114 actual vias: 641 x 0.20 mm, 472 x 0.30 mm, 1 x 0.40 mm.
Leave all 109 plated component holes/slots and 56 NPTH holes open.
See via-treatment.svg and do-not-fill-holes.csv. These agree with the
ViaDrill/ComponentDrill attributes in the Excellon files; diagrams use positive
Y downward, while the supplied Gerber/Excellon Y coordinates are negative.
In particular, the 86 labelled solder-wire holes on J2/J3/J4/J6/J7/J8/J9/J10/J11
are plated component holes, not vias: requested finished diameters 0.8 mm
signal / 1.1 mm power, with matching nominal Excellon values. Confirm your
drill compensation and finished-hole tolerance after plating.
They must remain open, exposed on both faces and free of paste apertures.

Please review the three stencil groups, paste-only variant and U32/optical
exclusions, and absence of paste on all nine wire arrays. **0.10 mm — selected
for Rev-A prototype**, uniform stainless steel; do not substitute 0.125 mm or
resize apertures automatically. The encoder's minimum area ratio is 0.7752
at 0.10 mm versus 0.6202 at 0.125 mm. See STENCIL_REVIEW.md for the deliberate
20% lower nominal paste volume versus the same openings in TI's 0.125 mm
DSG/RTE/RGF examples. Confirm manufacture of the supplied aperture geometry;
report any specific production constraint before changing it.
Practice printing and reflow remain our assembly tasks.
Provide final group coordinates if rearrangement is required, so we can
regenerate the alignment jig. Do not change apertures without review.
Prefer retaining the supplied groups and relative orientation; global sheet
centering is acceptable. Please disable automatic aperture optimization.

Package identity (filled automatically in the exported draft):

- Gerber/drill ZIP SHA-256: {{GERBER_SHA256}}
- Stencil ZIP SHA-256: {{STENCIL_SHA256}}
- Source/transform authority: panel-manifest.json
- All-file hashes: file-sha256.json

Prepared attachments: both ZIPs, MANUFACTURING_NOTES.md, panel-mechanical.svg,
panel-manifest.json, all-vias.csv, STENCIL_REVIEW.md, stencil-support-jig.svg,
paste-shape-measurements.csv and paste-land-coverage.csv.
The consolidated CAM-review-attachments.zip also includes order-settings.json,
STACK_AND_LAYERS.md, via-treatment.svg and do-not-fill-holes.csv, with an internal
attachment-sha256.json for verification. It is a review bundle: use its enclosed
PCB Gerber ZIP for PCB upload and its enclosed stencil ZIP for stencil upload.

Please return explicit acceptance or a list of required changes against these
exact files. A price quotation alone will not be treated as CAM acceptance.
