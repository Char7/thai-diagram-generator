# thai-diagram-generator (alpha)

An offline Agent Skill for static educational diagrams. It generates editable SVG and HTML along with Thai-readable Windows PNG, using a reusable JSON input spec instead of hard-coded PC2 paths or original T01–T03 contents.

## Tested now
- Three synthetic demo diagrams: Mind Map, Flowchart and scientific diagram with new locally drawn demo PNG.
- Automated QA: text versus connector clearance, image original/display ratio, source version protection.
- Windows PNG rendering: native GDI+ shaping of Thai labels, PyMuPDF for nontext graphic layers.
- Unit and isolated project smoke tests run on PC2.

## Example usage
    python scripts/diagram_cli.py --spec examples/mindmap.json --output-dir C:\Temp\my-diagram-output --stem my_mindmap_v01
    python -m unittest discover -s tests -v

For another project: supply a JSON spec with image paths relative to that spec. Source files can live anywhere; CLI locates package scripts relative to its own directory.

## Agent Skill installation
The root contains SKILL.md as the Agent Skills entry point. Clone or copy this repository to your Agent's configured skills directory, using the current supported workflow. Verify discovery and actual invocation before advertising one-line installation commands.

## Data protection
Only synthetic example data is included in this repository. Do NOT commit private documents, unrelated project inputs, original book illustrations, user-specific paths or secrets.

## Release gates
- LICENSE not yet chosen; public visibility does not itself grant open-source reuse rights
- External agent/Skill discovery and runtime validation
- Independent SVG rendering / Thai glyph verification
- Robust test of cross-machine installation; non-Windows PNG support still unavailable
- Automated QA must not be represented as scientific QA or manual visual approval
- Source repository may be public, but no stable release is tagged; this code remains alpha

Read SKILL.md and references/QUALITY_RULES.md before using it.
