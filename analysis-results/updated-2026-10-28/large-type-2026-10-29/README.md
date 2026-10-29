# 大字版响应面图（2026-10-29）

## 直接下载

- [PPT大字版](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/large-type-2026-10-29/large_type_slides.pptx)
- [带完整标题和条件的PDF预览](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/large-type-2026-10-29/large_type_slides.pdf)
- [180mm论文排版PDF](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/large-type-2026-10-29/paper_layout_180mm.pdf)
- [高清图与SVG完整包](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/large-type-2026-10-29/large_type_bundle.zip)

本版针对“字体太小”重新排版，不是只增大源文件中的字号。原三联图拆为单图，F/P温度趋势分别一页；主要刻度、等高线和图例最终字号至少22pt，坐标名26–28pt。

- large_type_slides.pptx：11页图版，可按汇报需要选用。
- large_type_slides.pdf：PPT整页PDF，含中文标题、固定条件和三维轴释义，建议先查看。
- preview_*.png：整页预览示例。
- large_type_figures.pdf：11页图形，最终字号与PPT对应。
- figures：高清PNG及可编辑文字SVG。
- paper_layout_180mm.pdf/png：单独的180mm宽论文排版示例，字小于PPT版，供论文排版使用。
- font_size_audit.json：每张图最终字号和缩放倍数。
- format_references.md：格式参考、实际访问限制和字体说明。
- response_surface_readable.dxpx：与上一版相同的原生显示调整副本，字体偏好保存在用户软件内，尚未在DX13中试开。

图形全部使用上传项目完整精度数据及保存的F二次/P 2FI模型，数据、模型与优化设置不变。色面/曲线为条件均值预测；各固定C水平使用统一坐标和色标，灰区超出实验工况凸包。β数值版本差异仍按原项目保留，不据其作可靠优化。没有实际能耗数据。

复现：安装requirements.txt依赖后，运行 `python build_large_type.py source_project.dxpx --output regenerated`。

PPT整页PDF使用LibreOffice导出，命令：`soffice --headless --convert-to pdf --outdir . large_type_slides.pptx`。
