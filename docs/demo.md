# 演示素材与复现

README 中的 GIF 和 MP4 来自真实运行的 CleanCV 本地网页，包含实际 API 调用、检测结果和 PDF 导出，没有用静态画面伪装成功操作。

## 隐私与数据来源

- 录制只点击内置“载入虚构示例”，不打开用户 PDF。
- 简历由 `src/cleancv/demo.py` 从零生成：名字、学校、城市、项目与个人标识均为虚构。
- 邮箱使用保留域名 `example.com`；电话使用 `555-01xx` 虚构号段。
- 头像由几何 SVG 图形生成，不对应真实人物。
- 浏览器使用新的临时 context，不加载个人浏览器 profile、Cookie 或已登录账号。
- 录制范围为网页 viewport，不包含地址栏或会话令牌；标题栏仅用于解释操作步骤。
- MP4/GIF 编码时清除输入媒体元数据。录制中间文件、导出 PDF 和审查帧都位于被忽略的 `private/demo/`。
- 只有明确命名的三个媒体文件获得 `.gitignore` 放行；发布前复查源码、关键帧、媒体元数据和最终 Git 提交。

## 录制流程

1. 载入完全虚构的示例。
2. 核查自动识别的姓名、电话、邮箱、政治身份和照片候选。
3. 撤销项目正文中的误报：正文里的“群众”不是个人政治身份。
4. 添加 `demo_profile` 为额外词，并重新识别。
5. 手动框选“所在地”。
6. 确认已逐页核查，生成 PDF。
7. 查看真实导出的处理结果。

脚本会验证自动字段存在、撤销决定没有被重置、额外词和手动框选生效、下载成功、结果预览显示，以及没有浏览器脚本错误。静态海报在独立的非录制 context 中截取，避免录屏出现布局跳动。

## 本地复现

工具本身不依赖 Node、Playwright 或 FFmpeg；它们只用于开发录制。

```bash
python -m pip install -e .
npm install --prefix .demo-tools playwright
NODE_PATH=.demo-tools/node_modules node .demo-tools/node_modules/playwright/cli.js install chromium
NODE_PATH=.demo-tools/node_modules node scripts/record-demo.cjs
python scripts/encode-demo.py
```

编码需要支持 H.264 和 GIF 的 FFmpeg。也可以安装 `imageio-ffmpeg`，编码脚本会自动寻找其二进制文件。

可选环境变量：

- `CHROMIUM_EXECUTABLE`：使用已有的 Chromium 可执行文件。
- `PLAYWRIGHT_BROWSERS_PATH`：Playwright 浏览器及录制编码器缓存路径。
- `PYTHON`：启动本地服务的 Python 可执行文件。
- `FFMPEG_BINARY`：编码脚本使用的 FFmpeg 路径。

录制脚本自动启动并停止自己的本地服务。运行 `node scripts/record-demo.cjs --inspect` 可检查 1440、1024、801、800 和 390 px 宽度的布局，验证手机端导出、视图切换、清空、键盘标签操作、拖放与文件选择导入及无外部请求，并将截图与检查结果保存在 `private/demo/`，不录制视频。

## 文件

- `media/cleancv-demo.gif`：README 内联播放。
- `media/cleancv-demo.mp4`：高清可播放视频。
- `media/cleancv-poster.png`：静态界面。
- `media/cleancv-mark.svg`：项目自己的图标。

README 的“简介—入口—界面展示—快速开始”组织方式参考了用户指定的 t3code 项目；没有复用其代码、Logo 或品牌素材。
