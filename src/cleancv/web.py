"""Single-user localhost UI. PDF bytes stay in memory; no third-party requests."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import hashlib
import json
import secrets
import webbrowser
from .core import MAX_BYTES, analyze, clean_pdf, render_preview, Region, CleanCVError
from .demo import create_demo_pdf


def create_server(port=8765):
    token = secrets.token_urlsafe(32)
    state = {"data": None, "id": None, "result": None}
    html = (Path(__file__).parent / "static" / "index.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log filenames, PDF text or personal terms.

        def send(self, status, payload, content_type="application/json"):
            if not isinstance(payload, bytes):
                payload = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(payload)

        def authorized(self):
            host = self.headers.get("Host", "")
            allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            if host not in allowed:
                self.send(403, {"error": "仅接受本机地址。"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + h for h in allowed}:
                self.send(403, {"error": "不接受跨站请求。"})
                return False
            supplied = self.headers.get("X-CleanCV-Token", "")
            if not secrets.compare_digest(supplied, token):
                self.send(403, {"error": "会话已失效，请使用终端输出的完整本地链接。"})
                return False
            return True

        def require_document(self, identity):
            if state["data"] is None or identity != state["id"]:
                raise CleanCVError("当前文档已改变，请重新打开 PDF。")
            return state["data"]

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                return self.send(200, html, "text/html; charset=utf-8")
            if not self.authorized():
                return
            try:
                if parsed.path.startswith(("/api/page/", "/api/result/")) and parsed.path.endswith(".png"):
                    number = int(parsed.path.rsplit("/", 1)[1][:-4])
                    identity = parse_qs(parsed.query).get("id", [None])[0]
                    data = self.require_document(identity)
                    if parsed.path.startswith("/api/result/"):
                        if state["result"] is None:
                            raise CleanCVError("尚未生成当前文档的脱敏结果。")
                        data = state["result"]
                    return self.send(200, render_preview(data, number), "image/png")
                self.send(404, {"error": "不存在的路径。"})
            except (ValueError, KeyError) as exc:
                self.send(400, {"error": str(exc) if isinstance(exc, CleanCVError) else "请求格式错误。"})

        def do_POST(self):
            if not self.authorized():
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > MAX_BYTES:
                    return self.send(413, {"error": "请求为空或超过 25 MB。"})
                body = self.rfile.read(size)
                if self.path == "/api/open":
                    result = analyze(body)
                    state.update(data=body, id=result.document_sha256, result=None)
                    return self.send(200, result.to_dict())
                if len(body) > 1024 * 1024:
                    raise CleanCVError("区域或额外词数据过大。")
                value = json.loads(body)
                if self.path == "/api/demo":
                    data = create_demo_pdf()
                    result = analyze(data)
                    state.update(data=data, id=result.document_sha256, result=None)
                    return self.send(200, result.to_dict())
                if self.path == "/api/clear":
                    state.update(data=None, id=None, result=None)
                    return self.send(200, {"ok": True})
                data = self.require_document(value.get("document_id"))
                if self.path == "/api/detect":
                    terms = value.get("terms", [])
                    if not isinstance(terms, list) or len(terms) > 100 or not all(isinstance(t, str) and 0 < len(t) <= 200 for t in terms):
                        raise CleanCVError("额外词格式错误或数量过多。")
                    return self.send(200, analyze(data, terms=terms).to_dict())
                if self.path == "/api/clean":
                    if value.get("reviewed") is not True:
                        raise CleanCVError("请先逐页核查，再勾选已检查。")
                    regions = [Region.from_dict(r) for r in value.get("regions", [])]
                    if not regions:
                        raise CleanCVError("还没有选中要移除的区域。")
                    scan_pages = [p["page"] for p in analyze(data).pages if p["scan_like"]]
                    if any(not any(r.page == p and r.kind == "manual" for r in regions) for p in scan_pages):
                        raise CleanCVError("扫描页需要手动框选；自动检测不能识别扫描图像里的姓名和照片。")
                    result = clean_pdf(data, regions, dpi=180, ocr=value.get("ocr") is True)
                    state["result"] = result
                    return self.send(200, result, "application/pdf")
                self.send(404, {"error": "不存在的路径。"})
            except (CleanCVError, ValueError, TypeError, KeyError) as exc:
                self.send(400, {"error": str(exc) if isinstance(exc, CleanCVError) else "请求格式错误。"})
            except Exception:
                self.send(500, {"error": "处理失败；请检查 PDF 或减少页面大小。没有上传或保存输入文件。"})

    # PyMuPDF is not thread safe. A single HTTPServer serializes all document operations.
    server = HTTPServer(("127.0.0.1", port), Handler)
    return server, token


def serve(port=8765, open_browser=False):
    if not 0 <= port <= 65535:
        raise CleanCVError("端口必须为 0–65535。")
    server, token = create_server(port)
    url = f"http://127.0.0.1:{server.server_port}/#token={token}"
    print("CleanCV 已在本机启动。输入文件仅保存在进程内存；清空或退出即释放。", flush=True)
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
