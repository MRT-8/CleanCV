"""Offline detection, redaction and PDF reconstruction. Never logs matched text."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import math
import re
import unicodedata
import fitz

MAX_BYTES = 25 * 1024 * 1024
MAX_PAGES = 30
MAX_PIXELS = 24_000_000


class CleanCVError(ValueError):
    pass


@dataclass(frozen=True)
class Region:
    # Public / UI coordinates are displayed-page coordinates, in PDF points.
    page: int
    rect: tuple[float, float, float, float]
    kind: str = "manual"
    confidence: str = "manual"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        try:
            page = value["page"]
            if isinstance(page, bool) or not isinstance(page, int):
                raise ValueError
            rect = tuple(float(v) for v in value["rect"])
            if len(rect) != 4 or not all(math.isfinite(v) for v in rect):
                raise ValueError
            # Ignore arbitrary labels from plans; reports never echo personal strings.
            kind = value.get("kind", "manual")
            if kind not in {"name", "email", "phone", "politics", "photo", "image", "extra", "manual"}:
                kind = "manual"
            confidence = value.get("confidence", "manual")
            if confidence not in {"high", "heuristic", "manual"}:
                confidence = "manual"
            return cls(page, rect, kind, confidence)
        except (KeyError, TypeError, ValueError) as exc:
            raise CleanCVError("区域格式错误：需要整数 page 和四个有限坐标 rect。") from exc


@dataclass
class Analysis:
    document_sha256: str
    pages: list[dict]
    regions: list[Region]
    warnings: list[str]

    def to_dict(self):
        return {"version": 1, "document_sha256": self.document_sha256,
                "pages": self.pages, "regions": [r.to_dict() for r in self.regions],
                "warnings": self.warnings}


def open_pdf(data: bytes):
    if not data or len(data) > MAX_BYTES:
        raise CleanCVError("文件为空或超过 25 MB。")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise CleanCVError("无法读取 PDF；请先将简历导出为有效 PDF。") from exc
    if not doc.is_pdf or doc.needs_pass or not 1 <= len(doc) <= MAX_PAGES:
        doc.close()
        raise CleanCVError("仅支持未加密、1–30 页的 PDF。")
    # Preserve the original visible appearance before inspecting or removing anything.
    # Deleting an opaque annotation could otherwise reveal sensitive text underneath.
    try:
        doc.bake(annots=True, widgets=True)
    except Exception as exc:
        doc.close()
        raise CleanCVError("无法安全固化批注/表单，请先使用 PDF 阅读器导出普通 PDF。") from exc
    return doc


def page_lines(page):
    result = []
    for block in page.get_text("rawdict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            chars, boxes, sizes = [], [], []
            for span in line["spans"]:
                for char in span["chars"]:
                    # Normalize compatibility characters while retaining char geometry.
                    for c in unicodedata.normalize("NFKC", char["c"]):
                        chars.append(c)
                        boxes.append(fitz.Rect(char["bbox"]))
                        sizes.append(span["size"])
            if chars:
                result.append(("".join(chars), boxes, max(sizes)))
    return result


EMAIL = re.compile(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}")
PHONES = [
    re.compile(r"(?<!\d)(?:\+?86[ -]*)?1[3-9](?:[ -]?\d){9}(?!\d)"),
    re.compile(r"(?<!\d)(?:\+?86[ -]*)?0\d{2,3}[ -]?\d{7,8}(?!\d)"),
    re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)"),
    re.compile(r"(?<!\w)\+\d[\d ().-]{6,24}\d(?!\d)"),
]
POLITICS = re.compile(r"中共(?:预备)?党员|共青团员|无党派(?:人士)?|民主党派|群众|(?<!共青)团员|(?i:political\s*(?:affiliation|status)\s*[:：]\s*[^|;；\n]+)")
NAME_LABEL = re.compile(r"(?:姓名|(?i:full\s*name|name))\s*[:：]\s*([^|;；,，\n]{1,50})")
NAME_EXCLUDE = re.compile(r"简历|履历|研究|教育|经历|技能|大学|学院|专业|工程|算法|求职|目标|开发|安全|自我|介绍|(?i:resume|curriculum|vitae|engineer|developer|experience|education|skills|profile|summary)")
NAME_SHAPE = re.compile(r"(?:[\u4e00-\u9fff·]{2,8}|[A-Za-z][A-Za-z .'-]{1,49})\Z")


def analyze(data: bytes, names=(), terms=(), images="header") -> Analysis:
    if images not in {"header", "all", "none"}:
        raise CleanCVError("图片策略必须是 header、all 或 none。")
    regions, pages, warnings = [], [], []
    detected_names = set(str(x).strip() for x in names if str(x).strip())
    all_lines = []
    with open_pdf(data) as doc:
        for index, page in enumerate(doc):
            lines = page_lines(page)
            all_lines.append(lines)
            bounds = page.rect
            im = page.get_image_info()
            large_image = any((fitz.Rect(i["bbox"]) * page.rotation_matrix).get_area() > bounds.get_area() * .7 for i in im)
            scan_like = sum(len(t.strip()) for t, _, _ in lines) < 20 or large_image
            pages.append({"page": index + 1, "width": bounds.width, "height": bounds.height, "scan_like": scan_like})
            if scan_like:
                warnings.append(f"第 {index + 1} 页疑似扫描件：文字与照片自动检测可能遗漏，请手动框选并逐页检查。")
            if index == 0:
                candidates = []
                for text, boxes, size in lines:
                    value = text.strip()
                    rect = fitz.Rect(boxes[0])
                    for box in boxes[1:]:
                        rect |= box
                    view = rect * page.rotation_matrix
                    if view.y0 < bounds.height * .28 and size >= 12 and NAME_SHAPE.fullmatch(value) and not NAME_EXCLUDE.search(value):
                        candidates.append((size, value))
                if candidates:
                    largest = max(s for s, _ in candidates)
                    detected_names.update(t for s, t in candidates if s >= largest - .2)
            for text, _, _ in lines:
                for match in NAME_LABEL.finditer(text):
                    value = match[1].strip()
                    if NAME_SHAPE.fullmatch(value):
                        detected_names.add(value)
            if images != "none":
                for image in im:
                    rect = (fitz.Rect(image["bbox"]) * page.rotation_matrix) & bounds
                    if rect.is_empty:
                        continue
                    ratio = rect.width / rect.height
                    header_photo = index == 0 and rect.y0 < bounds.height * .32 and .35 < ratio < 2.2 and rect.width >= 18 and rect.height >= 24 and rect.get_area() < bounds.get_area() * .3
                    if images == "all" or header_photo:
                        regions.append(Region(index + 1, tuple(rect), "photo" if header_photo else "image", "heuristic"))
        if not detected_names:
            warnings.append("未可靠定位姓名；可用 --name、额外移除词或手动框选补充。")
        for index, page in enumerate(doc):
            for text, boxes, _ in all_lines[index]:
                variants = [(text, boxes)]
                compact = [(c, b) for c, b in zip(text, boxes) if not c.isspace()]
                if compact:
                    variants.append(("".join(c for c, _ in compact), [b for _, b in compact]))
                patterns = [("email", EMAIL, "high"), ("politics", POLITICS, "high")]
                patterns += [("phone", p, "high") for p in PHONES]
                for value in detected_names:
                    # Explicit names are matched everywhere, including publication authors.
                    patterns.append(("name", re.compile(re.escape(unicodedata.normalize("NFKC", value)), re.I), "heuristic"))
                    if " " in value:
                        patterns.append(("name", re.compile(re.escape(re.sub(r"\s+", "", value)), re.I), "heuristic"))
                patterns += [("extra", re.compile(re.escape(unicodedata.normalize("NFKC", str(v))), re.I), "manual") for v in terms if str(v)]
                for string, mapping in variants:
                    for kind, pattern, confidence in patterns:
                        for match in pattern.finditer(string):
                            if kind == "phone" and not 7 <= len(re.sub(r"\D", "", match[0])) <= 15:
                                continue
                            area = fitz.Rect(mapping[match.start()])
                            for box in mapping[match.start()+1:match.end()]:
                                area |= box
                            # Small padding removes antialiased glyph edges.
                            area += (-.6, -.4, .6, .4)
                            area = (area * page.rotation_matrix) & page.rect
                            if not area.is_empty:
                                regions.append(Region(index + 1, tuple(area), kind, confidence))
    unique = {}
    for region in regions:
        key = (region.page, region.kind, tuple(round(v, 1) for v in region.rect))
        unique[key] = region
    return Analysis(hashlib.sha256(data).hexdigest(), pages, list(unique.values()), warnings)


def validate_regions(doc, regions):
    if len(regions) > 3000:
        raise CleanCVError("区域数量超过限制。")
    for region in regions:
        if not 1 <= region.page <= len(doc):
            raise CleanCVError("区域页码超出文档范围。")
        rect = fitz.Rect(region.rect)
        bounds = doc[region.page - 1].rect
        if not rect.is_valid or rect.is_empty or not all(math.isfinite(v) for v in rect):
            raise CleanCVError("区域坐标无效。")
        if not bounds.contains(rect):
            raise CleanCVError("区域超出页面范围，请在预览中重新框选。")


def render_preview(data, page_number, max_width=1200):
    with open_pdf(data) as doc:
        if not 1 <= page_number <= len(doc):
            raise CleanCVError("页码无效。")
        page = doc[page_number - 1]
        scale = min(max_width / page.rect.width, 1600 / page.rect.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        return pix.tobytes("png")


def clean_pdf(data: bytes, regions, dpi=180, fill="white", ocr=False, language="chi_sim+eng") -> bytes:
    if isinstance(dpi, bool) or not isinstance(dpi, int) or not 96 <= dpi <= 300:
        raise CleanCVError("DPI 必须是 96–300 之间的整数。")
    if fill not in {"white", "black"}:
        raise CleanCVError("遮除颜色只能是 white 或 black。")
    color = (1, 1, 1) if fill == "white" else (0, 0, 0)
    with open_pdf(data) as source, fitz.open() as output:
        validate_regions(source, regions)
        for index in range(len(source)):
            page = source[index]
            # open_pdf already baked visible annotations and form fields into this copy.
            for region in regions:
                if region.page == index + 1:
                    rect = fitz.Rect(region.rect) * page.derotation_matrix
                    page.add_redact_annot(rect, fill=color, cross_out=False)
            page.apply_redactions(images=2, graphics=0, text=0)
            page = source.reload_page(page)
            scale = dpi / 72
            if page.rect.width * page.rect.height * scale * scale > MAX_PIXELS:
                raise CleanCVError("页面像素过大，请降低 DPI 或缩小页面尺寸。")
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False, annots=False)
            pix.set_dpi(dpi, dpi)
            if ocr:
                # OCR only sees the already-redacted pixels; original hidden text is never copied.
                try:
                    ocr_data = pix.pdfocr_tobytes(language=language)
                except Exception as exc:
                    raise CleanCVError("本地 OCR 不可用：请安装 Tesseract 语言数据并配置 TESSDATA_PREFIX，或取消 --ocr。") from exc
                with fitz.open(stream=ocr_data, filetype="pdf") as ocr_doc:
                    output.insert_pdf(ocr_doc)
            else:
                fresh = output.new_page(width=page.rect.width, height=page.rect.height)
                fresh.insert_image(fresh.rect, stream=pix.tobytes("png"))
        output.set_metadata({"title": "Anonymized resume", "creator": "CleanCV", "producer": "CleanCV"})
        output.set_toc([])
        return output.tobytes(garbage=4, deflate=True)
