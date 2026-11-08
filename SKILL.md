---
name: thai-diagram-generator
description: Create editable SVG mind maps, flowcharts, and scientific diagrams with correctly shaped Thai PNGs on Windows. Check text/connector collisions and preserve inserted image aspect ratios.
---

# Thai Diagram Generator — alpha

This Skill generates editable static SVG diagrams plus HTML and Windows GDI+-rendered Thai PNG. It does NOT need HyperFrames and is not yet production-approved.

## Prerequisites
- Python 3.11+ with PyMuPDF and Pillow as specified in requirements.txt.
- Windows with PowerShell 5.1+ and installed Tahoma font family for native GDI+ PNG.
- macOS/Linux: use --svg-only; independently verify Thai shaping in the target viewer.

## Mandatory quality rules
1. Thai combining marks (especially เลี้ยง, เชื่อม, เงื่อนไข, เมล็ด) must be visually correct; inspect final PNG at full resolution and zoom. SVG source validity alone is insufficient.
2. No text may overlap any connector, arrow, line or decision branch. The numeric test uses minimum 16 SVG coordinate units of label-line clearance.
3. Images always use proportional CONTAIN scaling, preserving source width/height. Aspect tolerance at most 0.5%. No stretching or cropping for convenience.
4. Preserve original assets and all older versions. Use unique versioned stems.
5. Technical QA PASS is not final scientific, print or owner acceptance. Inspect both PNG and independent SVG rendering.

## Input: JSON diagram specification
Read examples/mindmap.json, examples/flowchart.json and examples/scientific.json.

Key fields:
- canvas: width and height in SVG coordinate units (e.g. 1400x1980 for A4 portrait).
- shapes: rect, ellipse or diamond at x,y,w,h.
- connectors: polyline points as [x,y] list plus arrow boolean.
- texts: value,x,y,size,anchor,bold,color. Each label independently editable as SVG text.
- images: a relative image file and a bounding box x,y,w,h. Layout automatically preserves source aspect ratio.

Create source specs in YOUR project. Do not put private textbooks or scanned pages into the reusable Skill.

## Run
Windows, from Skill directory:

    python scripts/diagram_cli.py --spec examples/mindmap.json --output-dir examples_out --stem mindmap_v01
    python scripts/diagram_cli.py --spec examples/flowchart.json --output-dir examples_out --stem flowchart_v01
    python scripts/diagram_cli.py --spec examples/scientific.json --output-dir examples_out --stem science_v01

Non-Windows (SVG and HTML only):

    python scripts/diagram_cli.py --spec examples/mindmap.json --output-dir examples_out --stem mindmap_v01 --svg-only

Run tests:

    python -m unittest discover -s tests -v

## Outputs
- stem.svg: editable text, shapes, connector and embedded illustration
- stem.html: local SVG viewer wrapper
- stem.png: Windows GDI+ Thai text overlay on SVG background (Windows only)
- stem.qa.json: technical checks and explicit visual_qa=PENDING status
- stem.text.json / stem.bbox.json / stem.background.png: reproducible intermediates

## Agent acceptance protocol
1. Read references/QUALITY_RULES.md and references/QA_CHECKLIST.md.
2. Run package tests and a real separate-project example.
3. Check report: pass=true, collisions=[], aspect_failures=[].
4. Open actual PNG and inspect tone marks, labels, arrowheads and illustrations.
5. Inspect SVG in the intended editor/browser separately. Thai SVG shaping is not fully validated across viewers.
6. Log scientific/editorial review and owner acceptance separately; never fabricate PASS.

## Limitations
- This is spec-driven, not natural-language-to-diagram; use the agent to create the JSON spec first.
- QA currently checks text against connector segments and bitmap aspect, not every text/shape-border interaction or glyph formation. Visual review is mandatory.
- PNG renderer is Windows only. SVG editing works elsewhere, but target-viewer Thai correctness is unverified.
- No HyperFrames, Office/Word export, GitHub publish or speed benchmark in alpha.
