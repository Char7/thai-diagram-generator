"""Thai Diagram Generator alpha — generic static SVG diagram authoring and validation.

Independent of DiagramPipelineLab / T01-T03; offline. PNG text uses Windows GDI+.
Do not treat structural PASS as scientific or visual QA approval.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

COLORS = re.compile(r"^#[0-9A-Fa-f]{6}$")
ROOT = Path(__file__).resolve().parent.parent
NS = {"svg": "http://www.w3.org/2000/svg"}
TEXT_RE = re.compile(r"<text\b[^>]*>.*?</text>", flags=re.S)


class DiagramError(ValueError):
    pass


def color(value: str) -> str:
    if not COLORS.fullmatch(value):
        raise DiagramError(f"Invalid hex color: {value!r}")
    return value


def number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DiagramError(f"{label} must be a finite number")
    return float(value)


def positive(value, label: str) -> float:
    val = number(value, label)
    if val <= 0:
        raise DiagramError(f"{label} must be positive")
    return val


def fmt(n) -> str:
    return f"{float(n):.3f}".rstrip("0").rstrip(".")


def element_text(t: dict, font: str) -> str:
    value = str(t["value"])
    if not value.strip():
        raise DiagramError("Text must be nonempty")
    if "\n" in value or "\r" in value:
        raise DiagramError("Use separate labels for separate lines; do not split Thai words")
    x, y = number(t["x"], "text.x"), number(t["y"], "text.y")
    size = positive(t.get("size", 36), "text.size")
    weight = 700 if t.get("bold", False) else 400
    anchor = t.get("anchor", "start")
    if anchor not in ("start", "middle", "end"):
        raise DiagramError("text.anchor must be start|middle|end")
    fill = color(t.get("color", "#13223B"))
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(size)}" '
            f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}" '
            f'font-family="{escape(font, quote=True)}">{escape(value)}</text>')


def fit_image(image_path: Path, box: dict) -> dict:
    from PIL import Image
    with Image.open(image_path) as im:
        source_w, source_h = im.size
    x, y = number(box["x"], "image.box.x"), number(box["y"], "image.box.y")
    bw, bh = positive(box["w"], "image.box.w"), positive(box["h"], "image.box.h")
    s = min(bw / source_w, bh / source_h)
    w, h = source_w * s, source_h * s
    result = dict(x=x + (bw-w)/2, y=y + (bh-h)/2, width=w, height=h,
                  source_width=source_w, source_height=source_h,
                  aspect_error=abs((w/h)/(source_w/source_h)-1.0))
    if result["aspect_error"] > 0.005:
        raise DiagramError("Image aspect ratio exceeds 0.5% tolerance")
    return result


def build_svg(spec: dict, source_file: Path) -> tuple[str, list[dict]]:
    canvas = spec.get("canvas", {})
    width = positive(canvas.get("width", 1400), "canvas.width")
    height = positive(canvas.get("height", 1980), "canvas.height")
    if width > 8000 or height > 8000:
        raise DiagramError("Maximum canvas size is 8000 units")
    font = str(spec.get("font", "Tahoma"))
    background = color(spec.get("background", "#FFFFFF"))
    parts = [
        f'<rect width="{fmt(width)}" height="{fmt(height)}" fill="{background}"/>'
    ]
    raster_assets = []
    for s in spec.get("shapes", []):
        kind = s.get("type", "rect")
        x, y = number(s["x"], "shape.x"), number(s["y"], "shape.y")
        w, h = positive(s["w"], "shape.w"), positive(s["h"], "shape.h")
        stroke = color(s.get("stroke", "#D9E4F1"))
        fill = color(s.get("fill", "#F4F8FC"))
        sw = number(s.get("stroke_width", 2), "shape.stroke_width")
        if sw < 0:
            raise DiagramError("shape.stroke_width must be >=0")
        if kind == "rect":
            radius = number(s.get("radius", 20), "shape.radius")
            parts.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
                         f'rx="{fmt(radius)}" fill="{fill}" stroke="{stroke}" stroke-width="{fmt(sw)}"/>')
        elif kind == "ellipse":
            parts.append(f'<ellipse cx="{fmt(x+w/2)}" cy="{fmt(y+h/2)}" rx="{fmt(w/2)}" '
                         f'ry="{fmt(h/2)}" fill="{fill}" stroke="{stroke}" stroke-width="{fmt(sw)}"/>')
        elif kind == "diamond":
            points = f'{fmt(x+w/2)},{fmt(y)} {fmt(x+w)},{fmt(y+h/2)} {fmt(x+w/2)},{fmt(y+h)} {fmt(x)},{fmt(y+h/2)}'
            parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{fmt(sw)}"/>')
        else:
            raise DiagramError(f"Unsupported shape type: {kind}")
    for path_item in spec.get("connectors", []):
        points = path_item.get("points", [])
        if len(points) < 2:
            raise DiagramError("Connector requires at least two points")
        pts = [(number(p[0], "connector.x"), number(p[1], "connector.y")) for p in points]
        stroke = color(path_item.get("color", "#7194B6"))
        sw = positive(path_item.get("width", 5), "connector.width")
        coords = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
        parts.append(f'<polyline points="{coords}" stroke="{stroke}" stroke-width="{fmt(sw)}" '
                     f'fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
        if path_item.get("arrow", True):
            ax, ay = pts[-1]
            bx, by = pts[-2]
            length = math.hypot(ax-bx, ay-by)
            if length < 1e-6:
                raise DiagramError("Connector last segment cannot have zero length")
            ux, uy = (ax-bx)/length, (ay-by)/length
            size = sw * 3.4
            left = (ax-size*ux+0.5*size*uy, ay-size*uy-0.5*size*ux)
            right = (ax-size*ux-0.5*size*uy, ay-size*uy+0.5*size*ux)
            polygon = f'{fmt(ax)},{fmt(ay)} {fmt(left[0])},{fmt(left[1])} {fmt(right[0])},{fmt(right[1])}'
            parts.append(f'<polygon points="{polygon}" fill="{stroke}"/>')
    for im in spec.get("images", []):
        if set(im).difference({"file", "box"}):
            raise DiagramError("Image only supports file and contain box; no independent axis scaling")
        rel = Path(im["file"])
        asset = (source_file.parent / rel).resolve()
        if not asset.is_file():
            raise DiagramError(f"Missing image asset: {asset}")
        loc = fit_image(asset, im["box"])
        extension = asset.suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise DiagramError("Only PNG/JPEG/WebP supported for embedded images")
        mimetype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[extension]
        b64 = base64.b64encode(asset.read_bytes()).decode("ascii")
        parts.append(f'<image x="{fmt(loc["x"])}" y="{fmt(loc["y"])}" '
                     f'width="{fmt(loc["width"])}" height="{fmt(loc["height"])}" '
                     f'preserveAspectRatio="xMidYMid meet" '
                     f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                     f'xlink:href="data:{mimetype};base64,{b64}"/>')
        raster_assets.append({"file": str(rel), "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
                              **loc})
    for t in spec.get("texts", []):
        parts.append(element_text(t, font))
    if not spec.get("texts"):
        raise DiagramError("Diagram needs at least one editable text label")
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(width)}" height="{fmt(height)}" '
           f'viewBox="0 0 {fmt(width)} {fmt(height)}">'
           + "".join(parts) + "</svg>")
    ET.fromstring(svg.encode("utf-8"))
    return svg, raster_assets


def parse_points(item: str) -> list[tuple[float, float]]:
    return [tuple(map(float, xy.split(","))) for xy in item.strip().split()]


def segment_hit(rect: dict, a: tuple[float, float], b: tuple[float, float],
                pad: float) -> bool:
    # Liang–Barsky line clipping, handles diagonal segments exactly.
    x0, y0 = a
    dx, dy = b[0]-x0, b[1]-y0
    xmin, ymin = rect["x"]-pad, rect["y"]-pad
    xmax = rect["x"]+rect["width"]+pad
    ymax = rect["y"]+rect["height"]+pad
    lo, hi = 0.0, 1.0
    for p, q in [(-dx, x0-xmin), (dx, xmax-x0), (-dy, y0-ymin), (dy, ymax-y0)]:
        if abs(p) < 1e-10:
            if q < 0:
                return False
        else:
            r = q/p
            if p < 0:
                lo = max(lo, r)
            else:
                hi = min(hi, r)
            if lo > hi:
                return False
    return True


def geometry_qa(svg_file: Path, bboxes: list[dict], assets: list[dict],
                clearance: float = 16.0) -> dict:
    root = ET.parse(svg_file).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    connectors = []
    for node in root.iter(ns+"polyline"):
        pts = parse_points(node.get("points", ""))
        connectors.extend(zip(pts[:-1], pts[1:]))
    collisions = []
    for t in bboxes:
        for i, (a, b) in enumerate(connectors):
            if segment_hit(t, a, b, clearance):
                collisions.append({"text": t["text"], "connector_segment": i})
    image_failed = [asset for asset in assets if asset["aspect_error"] > 0.005]
    return {"pass": not collisions and not image_failed, "collisions": collisions,
            "aspect_failures": image_failed, "image_count": len(assets),
            "checked_labels": len(bboxes), "connector_segments": len(connectors),
            "clearance_units": clearance,
            "limitations": "Connector strokes/arrowheads approximated by 16-unit clearance; "
                           "label-to-shape borders, Thai glyph morphology and science meaning require visual QA."}


def create(spec_path: Path, output_dir: Path, stem: str, svg_only: bool = False) -> dict:
    spec_path = spec_path.resolve()
    if not spec_path.is_file():
        raise DiagramError(f"Spec not found: {spec_path}")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    svg, assets = build_svg(spec, spec_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / (stem+".svg")
    html_path = output_dir / (stem+".html")
    png_path = output_dir / (stem+".png")
    report_path = output_dir / (stem+".qa.json")
    paths = [svg_path, html_path, report_path] + ([] if svg_only else [png_path])
    if any(p.exists() for p in paths):
        raise DiagramError("Refusing to overwrite existing output (choose a new stem/version)")
    svg_path.write_text(svg, encoding="utf-8")
    html = ('<!DOCTYPE html><html lang="th"><meta charset="utf-8"><title>'
            + escape(stem) + '</title><body style="background:#eee;text-align:center">'
            + '<object style="width:min(98vw,760px)" data="'
            + escape(svg_path.name, quote=True) + '" type="image/svg+xml"></object></body></html>')
    html_path.write_text(html, encoding="utf-8")
    if svg_only:
        result = {"status": "SVG_CREATED_PNG_NOT_RENDERED", "svg": str(svg_path),
                  "html": str(html_path), "assets": assets,
                  "warning": "Must visually QA SVG Thai text in target viewer"}
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    if platform.system() != "Windows":
        raise DiagramError("PNG native Thai rendering currently requires Windows GDI+; use --svg-only")
    import fitz
    bare, count = TEXT_RE.subn("", svg)
    if count != len(spec["texts"]):
        raise DiagramError("Text extraction mismatch, PNG may be missing labels")
    bitmap_path = output_dir / (stem+".background.png")
    metadata_path = output_dir / (stem+".text.json")
    if bitmap_path.exists() or metadata_path.exists():
        raise DiagramError("Refusing to overwrite background or text metadata")
    doc = fitz.open(stream=bare.encode("utf-8"), filetype="svg")
    zoom = positive(spec.get("scale", 2), "scale")
    if zoom > 5:
        raise DiagramError("scale max is 5")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(str(bitmap_path))
    metadata_path.write_text(json.dumps({"image": str(bitmap_path), "png": str(png_path),
                                         "texts": spec["texts"], "scale": zoom,
                                         "font": spec.get("font", "Tahoma")},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
    overlay = ROOT / "scripts" / "render_native_thai.ps1"
    cp = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                         "Bypass", "-File", str(overlay), str(metadata_path),
                         str(output_dir / (stem+".bbox.json"))],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if cp.returncode:
        raise DiagramError(f"Native Thai render failed: {cp.stderr[-800:]}")
    bbox_file = output_dir / (stem+".bbox.json")
    boxes = json.loads(bbox_file.read_text(encoding="utf-8"))["boxes"]
    if len(boxes) != len(spec["texts"]):
        raise DiagramError("Native text bounding box count mismatch")
    # Restore authoritative Unicode labels from UTF-8 JSON; Windows PowerShell 5 can
    # serialize a lossy representation even when the PNG glyphs shape correctly.
    for box, label in zip(boxes, spec["texts"]):
        box["text"] = str(label["value"])
    normalized_bbox = output_dir / (stem+".bbox.normalized.json")
    if normalized_bbox.exists():
        raise DiagramError("Refusing to overwrite normalized bounding-box report")
    normalized_bbox.write_text(json.dumps({"renderer": "Windows GDI+", "boxes": boxes},
                                          ensure_ascii=False, indent=2), encoding="utf-8")
    qa = geometry_qa(svg_path, boxes, assets)
    qa.update({"status": "TECHNICAL_PASS_VISUAL_PENDING" if qa["pass"] else "TECHNICAL_FAIL",
               "svg": str(svg_path), "png": str(png_path), "text_bbox": str(normalized_bbox),
               "source_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
               "assets": assets, "visual_qa": "PENDING", "content_qa": "PENDING"})
    report_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline editable SVG + Windows native Thai PNG generator")
    parser.add_argument("--spec", required=True, type=Path, help="Independent JSON diagram specification")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--stem", required=True, help="Unique versioned output stem")
    parser.add_argument("--svg-only", action="store_true",
                        help="Generate editable SVG/HTML only (PNG unverified)")
    args = parser.parse_args()
    if not re.fullmatch(r"[\w.-]+", args.stem, flags=re.ASCII):
        parser.error("--stem must contain ASCII letters, digits, underscore, dot or hyphen")
    try:
        result = create(args.spec, args.output_dir.resolve(), args.stem, args.svg_only)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("pass", True) else 2
    except (DiagramError, ValueError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
