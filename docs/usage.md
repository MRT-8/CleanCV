# CleanCV 使用手册

**把简历交给 AI 之前，先在本机移除个人信息。**

CleanCV 接受 PDF 简历，自动定位姓名候选、电话、邮箱、政治身份和页首照片，支持手动框选与撤销，再生成新的脱敏 PDF。提供本地网页和命令行，不调用云端模型、分析服务或外部 OCR API。

> 自动识别不是完整匿名保证。姓名、图片和扫描内容可能漏检；学校、论文题目、项目链接也可能关联身份。导出前后都应逐页检查。

## 快速开始

需要 Python 3.10+：

```bash
python -m pip install -e .
cleancv serve --open-browser
```

已有 PyMuPDF 时，也可以直接：

```bash
python3 run.py
```

打开终端打印的完整链接。服务仅监听 `127.0.0.1:8765`，链接中的随机令牌用于当前本地会话。

1. 选择 PDF，自动生成敏感信息候选框。
2. 检查每一页；点击框内 **×** 撤销误报，在页面上拖动补框。
3. 在“额外移除内容”中填写姓名、微信号、个人主页等，每行一项。
4. 勾选已核查，下载 `resume-anonymized.pdf`，在结果预览中再次核查。

也可以点击“载入虚构示例”试用。示例由程序生成，不包含真实求职者的数据。撤销的自动候选不会因重新识别额外词而自动恢复。

输入文件只保留在进程内存，不写入上传目录；点击“重新开始”清空或停止本地服务后释放。预览和接口设置 `no-store`，网页不使用第三方字体、脚本或统计服务。本机系统的交换文件、浏览器和下载管理行为不在应用控制范围内。

在远程服务器运行时，使用 SSH 本地转发，例如 `ssh -L 8765:127.0.0.1:8765 your-server`；不要把服务开放到公网。

## 命令行

先检查候选信息数量，报告不打印匹配到的个人原文：

```bash
cleancv scan input.pdf --name "张三"
```

执行脱敏：

```bash
cleancv clean input.pdf -o resume-anonymized.pdf --name "张三"
```

补充其他可识别身份的文字和区域：

```bash
cleancv clean input.pdf -o resume-anonymized.pdf \
  --name "张三" \
  --term "my-personal-handle" \
  --box "1:490,25,565,115"
```

`--name` 和 `--term` 可重复。个人值写进命令参数后，可能被 shell 历史或本机进程列表记录；不希望在命令行留下这些值时，优先使用本地网页输入。不要把真实参数复制到公开 issue 或提交记录。

区域格式是 **页码:x0,y0,x1,y1**，页码从 1 开始，坐标以显示页面左上角为原点、单位为 PDF pt（1/72 英寸）。旋转页会自动转换到正确的内部坐标。

照片检测是基于位置和长宽比的候选判断，不做人脸识别：

- `--images header`：默认，标出首页顶部类似头像或二维码的图片，通常保留横向校徽。
- `--images all`：移除全部嵌入图片，包括校徽；对扫描件可能移除整页。
- `--images none`：不自动检测图片，改为手动框选。

### 保存和编辑区域计划

```bash
cleancv scan input.pdf --name "张三" --plan private/review.plan.json
cleancv clean input.pdf --plan private/review.plan.json -o resume-anonymized.pdf
```

计划包含页码、坐标、类别和输入文件 SHA-256，不保存匹配到的原文。可编辑 `regions` 增删区域；计划只接受同一个输入 PDF，防止对错误页面使用旧坐标。计划也可能暴露文档结构，请按私有文件保存。

### 扫描件

扫描图像内部的文字和人脸不会被当前自动规则读取。网页会提示手动框选；命令行默认拒绝未经确认的扫描页：

```bash
cleancv clean scan.pdf -o resume-anonymized.pdf \
  --box "1:150,20,580,130" --allow-scanned
```

每个扫描页都必须提供至少一个手动区域；这只是确认流程，仍需自行检查是否框全。

## 输出为什么默认不能复制文字？

脱敏先固化可见批注和表单，再应用 PDF redaction，再把**已处理的可见页面**渲染为像素，并用这些像素建立全新 PDF。原文件的文字层、图片对象、批注、表单、附件、链接、书签和元数据不会复制到输出中。

因此输出是图片型 PDF，版式仍在，但不能选中文字。AI 工具需要支持 PDF 图像理解或 OCR。它不是在原 PDF 上简单叠一个可移走的白块。

如果需要可复制文字，安装本地 Tesseract 语言数据、设置 `TESSDATA_PREFIX`，然后：

```bash
cleancv clean input.pdf --name "张三" --ocr --ocr-language chi_sim+eng
```

OCR 只读取已经脱敏后的画面，不使用原文件隐藏文字，也不调用外部服务。OCR 为可选功能；没有本地语言数据时会报错，不会降级调用云服务。识别文本可能有错，仍需检查。

其他选项：`--dpi 180`（范围 96–300）、`--fill black`、`--force`。默认拒绝覆盖已有输出，始终禁止覆盖输入 PDF。支持未加密的 1–30 页 PDF，最大 25 MB。

## 隐私边界

- 已选中区域会从最终画面和旧 PDF 对象层中移除；未被选中的可见信息仍会保留。
- 自动规则可能误报或漏报，不推断身份、不做人脸识别，不宣称能消除所有再识别风险。
- 先将批注和表单的可见外观固化到内存副本，保持原有遮挡效果，再定位和移除敏感信息；输出不保留交互功能或隐藏评论。
- 分享输出前，核查可见内容、文件名，以及论文作者、项目仓库、个人网址等间接身份信息。
- `.gitignore` 默认忽略 PDF、照片和 `private/`、`output/` 文件；这不阻止人为强制添加，提交前仍需检查暂存区。测试只使用程序生成的虚构样本。

## 开发与测试

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

测试覆盖个人信息定位、元数据/附件/链接清除、图片真实移除、旋转页与 CropBox 坐标、扫描件确认、区域计划绑定、原文件保护、本地接口令牌及跨站请求检查。OCR 的实际识别需要另行安装语言数据。

```text
src/cleancv/core.py       # 检测、区域校验、PDF 重建
src/cleancv/cli.py        # scan / clean / serve
src/cleancv/web.py        # 仅监听 localhost 的服务
src/cleancv/static/       # 无第三方资源的网页
```

## License

AGPL-3.0-only，见 [LICENSE](../LICENSE)。PDF 处理依赖 [PyMuPDF](https://github.com/pymupdf/PyMuPDF)。本项目按原样提供，不附带担保。

## 手机端操作

在“文档预览 / 核查与导出”之间切换。文档默认处于浏览模式；需要补框时开启画布工具栏的“框选”。支持缩放和页码跳转。导出后会切换到结果预览，在“导出与复查”中可再次下载或返回原稿。
