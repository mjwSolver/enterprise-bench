"""
Dual-Engine OCR & Document Screenshot Code Extractor
===================================================
Hardware-accelerated Apple Vision (Neural Engine) on macOS with Tesseract 5.5
cross-platform fallback, paired with code/config/SQL heuristic classification.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class OCRRecord:
    source_file: str
    engine: str
    width: int
    height: int
    is_code: bool
    code_score: int
    detected_indicators: List[str]
    extracted_text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodeClassifier:
    """Heuristic classifier to distinguish code/SQL/config from diagrams and slides."""

    CODE_KEYWORDS = [
        "import ", "from ", "def ", "class ", "spark", "sql", "select ", "from ", "where ",
        "pd.", "np.", "plt.", "sc.", "pyspark", "dataframe", "table", "config", "schema",
        "session", "yarn", "cloudera", "cdsw", "hadoop", "joblib", "pickle", "sklearn",
        "train", "predict", "cluster", "executor", "driver", "hive", "impala", "oracle",
        "return ", "for ", "in ", "if ", "elif ", "else:", "lambda ", "withColumn",
        "groupBy", "toPandas", "join(", "filter(", "getOrCreate", "enableHiveSupport"
    ]

    @classmethod
    def evaluate(cls, text: str) -> tuple[bool, int, List[str]]:
        if not text or len(text.strip()) < 10:
            return False, 0, []

        lower = text.lower()
        matched = [kw.strip() for kw in cls.CODE_KEYWORDS if kw in lower]
        score = len(matched)

        # Multi-line code block or distinct code patterns
        has_indent = bool(re.search(r"\n\s{2,8}\w+", text))
        has_assignment = bool(re.search(r"\w+\s*=\s*[\w\(\'\"]+", text))

        if has_indent:
            score += 1
        if has_assignment:
            score += 1

        is_code = score >= 2 or (score >= 1 and "\n" in text and len(text) > 40)
        return is_code, score, matched


class VisionOCREngine:
    """Dual-engine OCR processor supporting Apple Vision and Tesseract."""

    @staticmethod
    def _is_apple_vision_available() -> bool:
        if os.name != "posix" or subprocess.run(["uname", "-s"], capture_output=True, text=True).stdout.strip() != "Darwin":
            return False
        return shutil.which("swift") is not None

    @classmethod
    def run_apple_vision(cls, image_path: Path) -> str:
        """Execute Apple Vision VNRecognizeTextRequest via native Swift bridge."""
        swift_script = f"""
import Cocoa
import Vision

let imageURL = URL(fileURLWithPath: "{image_path.resolve()}")
guard let image = NSImage(contentsOf: imageURL),
      let tiffData = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let cgImage = bitmap.cgImage else {{
    exit(1)
}}

let request = VNRecognizeTextRequest {{ request, error in
    guard let observations = request.results as? [VNRecognizedTextObservation] else {{ return }}
    for observation in observations {{
        if let topCandidate = observation.topCandidates(1).first {{
            print(topCandidate.string)
        }}
    }}
}}

request.recognitionLevel = .accurate
request.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
"""
        try:
            res = subprocess.run(
                ["swift", "-e", swift_script],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @classmethod
    def run_tesseract(cls, image_path: Path) -> str:
        """Execute Tesseract OCR."""
        if not shutil.which("tesseract"):
            return ""
        try:
            res = subprocess.run(
                ["tesseract", str(image_path), "stdout", "--psm", "6"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return res.stdout.strip()
        except Exception:
            return ""

    @classmethod
    def process_image(
        cls,
        image_path: Path,
        engine_mode: str = "auto",
        filter_code_only: bool = False,
    ) -> Optional[OCRRecord]:
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                if w < 100 or h < 50:
                    return None
        except Exception:
            return None

        text = ""
        used_engine = engine_mode

        if engine_mode in ["auto", "apple-vision"]:
            if cls._is_apple_vision_available():
                text = cls.run_apple_vision(image_path)
                used_engine = "apple-vision"

        if not text and (engine_mode in ["auto", "tesseract"] or not text):
            text = cls.run_tesseract(image_path)
            used_engine = "tesseract"

        if not text:
            return None

        is_code, score, indicators = CodeClassifier.evaluate(text)

        if filter_code_only and not is_code:
            return None

        return OCRRecord(
            source_file=image_path.name,
            engine=used_engine,
            width=w,
            height=h,
            is_code=is_code,
            code_score=score,
            detected_indicators=indicators,
            extracted_text=text,
        )

    @classmethod
    def extract_docx_media(cls, docx_path: Path, output_dir: Path) -> List[Path]:
        """Extract media images from DOCX or PPTX archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted = []
        with zipfile.ZipFile(docx_path, "r") as z:
            for item in z.namelist():
                if item.startswith(("word/media/", "ppt/media/")) and item.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".tiff", ".bmp")
                ):
                    data = z.read(item)
                    dest = output_dir / Path(item).name
                    dest.write_bytes(data)
                    extracted.append(dest)
        return sorted(extracted)

    @classmethod
    def scan_path(
        cls,
        target_path: Path,
        engine_mode: str = "auto",
        filter_code_only: bool = False,
    ) -> List[OCRRecord]:
        """Scan a file (image, docx, pptx) or directory of images."""
        records: List[OCRRecord] = []

        if target_path.is_file():
            suffix = target_path.suffix.lower()
            if suffix in [".docx", ".pptx"]:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    media_files = cls.extract_docx_media(target_path, Path(tmp_dir))
                    for f in media_files:
                        rec = cls.process_image(f, engine_mode, filter_code_only)
                        if rec:
                            rec.source_file = f"{target_path.name}:{rec.source_file}"
                            records.append(rec)
            elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                rec = cls.process_image(target_path, engine_mode, filter_code_only)
                if rec:
                    records.append(rec)
        elif target_path.is_dir():
            files = sorted(
                [
                    p
                    for p in target_path.iterdir()
                    if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
                ]
            )
            for f in files:
                rec = cls.process_image(f, engine_mode, filter_code_only)
                if rec:
                    records.append(rec)

        return records
