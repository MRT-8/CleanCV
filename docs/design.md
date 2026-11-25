# 界面与流程设计

整体结构参考 [awesome-vibe-coding-websites](https://github.com/liyupi/awesome-vibe-coding-websites) 中 VibeFather 的以下项目：

| 参考 | 用于 CleanCV 的方向 |
|---|---|
| [Developer Utilities Toolbox](https://github.com/liyupi/awesome-vibe-coding-websites/tree/main/templates/developer-utilities-toolbox) | 清晰的工具布局、紧凑工具栏、直接操作工作区 |
| [Interactive Product Tour Page](https://github.com/liyupi/awesome-vibe-coding-websites/tree/main/templates/interactive-product-tour-page) | 按操作阶段组织入口、核查与结果 |
| [Resume Builder Web App](https://github.com/liyupi/awesome-vibe-coding-websites/tree/main/templates/resume-builder-web-app) | 纸张预览、文档工具与窄屏视图切换 |

这是 CleanCV 针对简历脱敏重新实现的页面与交互，未引入参考项目的提示词文本、源码、截图、字体或远程资源。参考项目的提示词与设计文档采用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)，不随本仓库分发。

## 三个状态

1. **导入首页**：选择或拖入 PDF，或载入虚构示例。首先呈现导入入口、操作步骤与本地处理说明。
2. **全屏核查**：左侧页码缩略图，中央简历画布，右侧候选类别与补充关键词。导出确认固定在右下方；画布和检查面板可分别滚动。
3. **结果复查**：画布与缩略图切换为实际导出内容，右侧显示下载状态、再次下载及返回原稿入口。继续编辑并更改标记后，旧结果失效，必须重新生成。

## 文档交互

- 点击候选类别定位并高亮对应区域；连续点击可依次定位该类候选。
- 点击页码缩略图或使用页码选择器跳转；支持多页 PDF。
- 画布可在 75%–200% 范围缩放，框选坐标始终换算为原始页面坐标。
- 红框为自动候选，绿色框为手动补充，点击框内 × 保留内容。
- 手机端使用“文档预览 / 核查与导出”切换，默认浏览模式；需要补框时开启“框选”。
- 点击“重新开始”清空当前文档并返回首页。关闭浏览器标签页不会自动停止本地 Python 服务。

## 资源与隐私

页面使用本机字体、原创 SVG 图标和 CSS。无第三方字体、统计服务或外部 API，不使用 localStorage 保存简历、关键词或历史记录。图片预览及生成结果仅在当前会话内使用，换文档或清空后释放相关引用。

真实录屏、首页及工作区截图见 [演示说明](demo.md)。
