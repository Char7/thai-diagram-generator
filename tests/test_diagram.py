"""Unit tests for reusable engine; all examples are synthetic, no school-source files."""
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import diagram_cli as g


class GeometryTests(unittest.TestCase):
    def test_0p5_percent_tolerance(self):
        with tempfile.TemporaryDirectory() as temp:
            png = Path(temp)/"synthetic.png"
            Image.new("RGB", (600,800)).save(png)
            fitted = g.fit_image(png, {"x":0,"y":0,"w":400,"h":800})
            self.assertAlmostEqual(fitted["width"]/fitted["height"], 0.75)
            self.assertAlmostEqual(fitted["aspect_error"], 0.0)

    def test_zero_width_image_box_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"a.png"
            Image.new("RGB",(10,20)).save(path)
            with self.assertRaises(g.DiagramError):
                g.fit_image(path, {"x":0,"y":0,"w":0,"h":300})

    def test_text_overlap_detection(self):
        rect={"x":100,"y":95,"width":60,"height":35}
        self.assertTrue(g.segment_hit(rect,(0,115),(250,115),16))
        self.assertFalse(g.segment_hit(rect,(0,10),(250,10),16))
        self.assertTrue(g.segment_hit(rect,(0,0),(200,200),16))

    def test_build_svg_generic_and_editable_text(self):
        spec={"canvas":{"width":500,"height":700}, "texts":[{"value":"ใบเลี้ยง", "x":50,"y":120}]}
        svg,assets=g.build_svg(spec,ROOT/"examples"/"mindmap.json")
        self.assertIn("ใบเลี้ยง",svg)
        self.assertIn("<text ",svg)
        self.assertEqual([],assets)

    def test_reject_unsafe_color(self):
        spec={"texts":[{"value":"ok","x":0,"y":30,"color":"red;onclick=evil"}]}
        with self.assertRaises(g.DiagramError):
            g.build_svg(spec,ROOT/"examples"/"mindmap.json")

    def test_reject_nonuniform_image_stretch_spec(self):
        spec={"texts":[{"value":"test","x":10,"y":50}],
              "images":[{"file":"assets/demo_plant.png",
                         "box":{"x":100,"y":100,"w":200,"h":400},
                         "scale_y":2}]}
        with self.assertRaises(g.DiagramError):
            g.build_svg(spec,ROOT/"examples"/"scientific.json")

    def test_wrong_svg_color_fails(self):
        with self.assertRaises(g.DiagramError):
            g.color("rgb(0,0,0)")


@unittest.skipUnless(platform.system()=="Windows","Native Thai PNG tests require Windows")
class IntegrationTests(unittest.TestCase):
    def test_run_independent_example_in_isolated_project(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"output"
            report=g.create(ROOT/"examples"/"mindmap.json",out,"fresh_sample_v01")
            self.assertTrue(report["pass"])
            self.assertEqual(report["visual_qa"],"PENDING")
            self.assertTrue((out/"fresh_sample_v01.svg").exists())
            self.assertTrue((out/"fresh_sample_v01.png").exists())
            with self.assertRaises(g.DiagramError):
                g.create(ROOT/"examples"/"mindmap.json",out,"fresh_sample_v01")

    def test_three_examples_in_new_project(self):
        with tempfile.TemporaryDirectory() as temp:
            # Copy only the demo input and locally authored asset, no Lab content.
            project=Path(temp)/"separate_project"
            project.mkdir()
            shutil.copytree(ROOT/"examples",project/"inputs")
            out=project/"output"
            for name in ("mindmap","flowchart","scientific"):
                result=g.create(project/"inputs"/(name+".json"),out,name+"_v01")
                self.assertTrue(result["pass"],(name,result["collisions"]))
                self.assertTrue((out/(name+"_v01.png")).is_file())
            sc=json.loads((out/"scientific_v01.qa.json").read_text(encoding="utf-8"))
            self.assertEqual(sc["image_count"],1)
            self.assertEqual(sc["assets"][0]["aspect_error"],0)

    def test_explicit_line_crossing_returns_qa_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            data={"canvas":{"width":500,"height":500},
                  "texts":[{"value":"ใช่","x":180,"y":260,"size":50}],
                  "connectors":[{"points":[[0,230],[450,230]]}]}
            sp=folder/"input.json"
            sp.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
            result=g.create(sp,folder/"out","collision_case")
            self.assertFalse(result["pass"])
            self.assertGreater(len(result["collisions"]),0)


if __name__=="__main__":
    unittest.main(verbosity=2)
