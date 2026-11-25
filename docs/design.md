# 界面设计

新版工作台参考 [awesome-vibe-coding-websites](https://github.com/liyupi/awesome-vibe-coding-websites) 中 VibeFather 的 [Resume Builder Web App](https://github.com/liyupi/awesome-vibe-coding-websites/tree/main/templates/resume-builder-web-app) 视觉方向：左侧编辑、右侧纸张预览，低干扰的编辑控件和深绿色画布。

CleanCV 围绕“导入—核查—导出”重新实现页面，沿用自己的盾牌图标、中文文案、虚构简历和 Python 本地处理。未引入模板源码、提示词文本、截图、字体或远程资源。参考项目的提示词与设计文档采用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)，不随本仓库分发。

## 使用方式

- 桌面端并排显示设置和文档，纸张区可独立滚动。
- 手机端使用“编辑与核查 / 文档预览”切换；默认允许滚动，开启“框选区域”后可拖动补框。
- 点击选择或拖入 PDF；“载入虚构示例”可体验整套流程。
- 查看候选数量、撤销误报、填写额外词，再确认已核查并导出。
- 导出后直接显示实际处理结果，可返回原稿继续编辑。
- 清空后恢复导入状态，释放服务端当前文档和结果。

## 视觉与资源

深绿色工作区、浅色编辑面板、细分隔线、克制的纸张阴影；统一行内 SVG 图标。所有字体使用本机字体栈，不请求 CDN、统计或外部服务。页面不使用 localStorage 保存简历或额外词。

真实操作的录屏与海报见 [演示说明](demo.md)。
