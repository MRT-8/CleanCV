"""Command-line interface; matched personal values are never printed."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import os
import sys
import tempfile
from .core import analyze, clean_pdf, CleanCVError, Region


def box(value):
    try:
        page, coordinates = value.split(":", 1)
        return Region.from_dict({"page": int(page), "rect": coordinates.split(",")})
    except (ValueError, CleanCVError) as exc:
        raise argparse.ArgumentTypeError("格式：页码:x0,y0,x1,y1，例如 1:250,40,350,85") from exc


def write_new(path, data, force=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not force:
        with path.open("xb") as file:
            file.write(data)
    else:
        fd, temporary = tempfile.mkstemp(prefix=".cleancv-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(data)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def parser():
    top = argparse.ArgumentParser(prog="cleancv", description="本地 PDF 简历脱敏：自动定位 + 手动补充 + 重建 PDF")
    sub = top.add_subparsers(dest="command", required=True)
    for command in ["scan", "clean"]:
        p = sub.add_parser(command, help="检查敏感区域" if command == "scan" else "输出脱敏 PDF")
        p.add_argument("input", type=Path)
        p.add_argument("--name", action="append", default=[], help="明确指定姓名，可重复")
        p.add_argument("--term", action="append", default=[], help="额外移除的原文，可重复")
        p.add_argument("--images", choices=["header", "all", "none"], default="header")
        p.add_argument("--box", type=box, action="append", default=[], help="手动区域：页码:x0,y0,x1,y1；页码从 1 开始")
        if command == "scan":
            p.add_argument("--plan", type=Path, help="保存不含匹配原文的区域计划")
        else:
            p.add_argument("-o", "--output", type=Path, default=Path("resume-anonymized.pdf"))
            p.add_argument("--plan", type=Path, help="使用 scan 导出的、可手工编辑的区域计划")
            p.add_argument("--allow-scanned", action="store_true", help="已人工核查扫描页；须同时提供手动区域")
            p.add_argument("--dpi", type=int, default=180)
            p.add_argument("--fill", choices=["white", "black"], default="white")
            p.add_argument("--ocr", action="store_true", help="对已脱敏画面执行本地 OCR，生成可复制文字")
            p.add_argument("--ocr-language", default="chi_sim+eng")
            p.add_argument("--force", action="store_true", help="替换已有输出，仍禁止覆盖输入")
    p = sub.add_parser("serve", help="启动仅监听 127.0.0.1 的本地网页")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--open-browser", action="store_true")
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "serve":
            from .web import serve
            serve(args.port, args.open_browser)
            return 0
        data = args.input.read_bytes()
        analysis = analyze(data, args.name, args.term, args.images)
        regions = analysis.regions + args.box
        if args.command == "clean" and args.plan:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            if plan.get("version") != 1 or plan.get("document_sha256") != hashlib.sha256(data).hexdigest():
                raise CleanCVError("计划与当前 PDF 不匹配，请重新 scan。")
            regions = [Region.from_dict(r) for r in plan["regions"]] + args.box
        if args.command == "scan":
            summary = analysis.to_dict()
            summary["regions"] = [r.to_dict() for r in regions]
            if args.plan:
                if args.plan.resolve() == args.input.resolve():
                    raise CleanCVError("计划文件不能覆盖原始 PDF。")
                write_new(args.plan, json.dumps(summary, ensure_ascii=False, indent=2).encode())
            print(json.dumps({"pages": len(analysis.pages), "counts": dict(Counter(r.kind for r in regions)), "warnings": analysis.warnings}, ensure_ascii=False, indent=2))
            return 0
        if args.output.resolve() == args.input.resolve():
            raise CleanCVError("禁止覆盖原始 PDF；请选择不同的输出路径。")
        if not regions:
            raise CleanCVError("未选中任何区域，请明确指定姓名、额外词或手动框选。")
        scans = [p["page"] for p in analysis.pages if p["scan_like"]]
        if scans and (not args.allow_scanned or any(not any(r.page == p and r.kind == "manual" for r in regions) for p in scans)):
            raise CleanCVError("检测到扫描页；请先用本地网页手动框选，或为每个扫描页提供 --box 并加 --allow-scanned。")
        for warning in analysis.warnings:
            print("注意：" + warning, file=sys.stderr)
        result = clean_pdf(data, regions, args.dpi, args.fill, args.ocr, args.ocr_language)
        write_new(args.output, result, args.force)
        print(f"已输出 {len(analysis.pages)} 页脱敏 PDF；处理 {len(regions)} 个候选区域。")
        print("请打开结果逐页核查。自动姓名/照片检测是启发式，论文、学校和项目链接也可能关联身份。")
        if not args.ocr:
            print("默认输出为图片型 PDF；使用支持图像/OCR 的 AI，或安装本地 OCR 后加 --ocr。")
        return 0
    except (CleanCVError, OSError, ValueError, KeyError, TypeError) as exc:
        # File errors can contain personal filenames; do not echo them.
        message = str(exc) if isinstance(exc, CleanCVError) else "文件读写或计划格式错误；请检查路径、权限及是否已存在同名输出。"
        print("CleanCV: " + message, file=sys.stderr)
        return 2
