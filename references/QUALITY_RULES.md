# Quality rules for all diagrams

Thai: Unicode text must be correct and visually inspectable. Do not split combining marks; verify real rendered PNG at full scale and zoom around เลี้ยง, เชื่อม, เงื่อนไข, เมล็ด. Editable SVG alone does not prove correct glyph shaping.

Labels: all text must be completely clear of connector lines, strokes and arrowheads. Automated line clearance is 16 SVG-coordinate units; validate shape/border overlaps by visual review. Place branch labels beside lines, never hide connectors with opaque label backgrounds.

Images: read source width/height and use one uniform contain-scale. Max relative ratio error ±0.5%, preferably exactly zero. Never stretch or crop away essential details. Preserve original image assets and separate editable text/connector layers.

Files: unique version stems, no deletes/overwrites, preserve provenance and QA evidence.

Approval: TECHNICAL_PASS_VISUAL_PENDING is NOT final acceptance. Domain and editorial QA and independent SVG/Word preview must be explicit.
