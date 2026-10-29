# 响应面图：突出条件变化规律

依据用户上传的 Design-Expert 13 原项目完整精度数据及其保存模型绘制。F使用完整二次；P使用原项目2FI；β不绘制可靠优化曲面。原文件、改图副本、源数据及验证记录均在包内。

## 直接下载

- [显示调整后的DX13项目](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/readable-graphs-2026-10-29/response_surface_readable.dxpx)
- [6页图版PPT](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/readable-graphs-2026-10-29/readable_graphs.pptx)
- [6页图PDF](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/readable-graphs-2026-10-29/readable_graphs.pdf)
- [完整图包ZIP](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/readable-graphs-2026-10-29/readable_graphs_bundle.zip)

## 使用文件
- `response_surface_readable.dxpx`：恢复显示范围和英文名称的项目副本。保留原固定初始氟含量0.8%。请用Design-Expert 13打开；本环境无法进行原软件试开验证。
- `readable_graphs.pdf`：6页图，已实际渲染检查。
- `figures/*.png`：适合PPT的高清图片。
- `figures/*.svg`：可编辑文字的矢量图，字体请求为Times New Roman；本机缺少该字体，PNG/PDF预览使用Liberation Serif替代。不能将预览称为真正的新罗马字体。
- `source_data.csv`、`source_project.dxpx`：本次来源数据及原项目。
- `readable_graphs.pptx`：6页图版，中文标题和说明可编辑；曲线的可编辑矢量版本见SVG。
- `verification.json`：逐字节保护校验、模型项、统计值及图形清单。

## 原项目修改范围
1. 恢复温度75–95°C、相比0.667–1.333；原项目只显示约77.95–83.21°C、1.21–1.39。
2. 因子/响应名称英文化，移除错误自定义标签。
3. 移除图例字号44/45的局部覆盖，继承软件全局字体；这些内部值的单位未验证，不能直接称为pt。
4. 刷新自动等高线缓存。未猜测原项目中未出现的Z轴、相机或字体族节点；重新绘制的附图则明确设置Z轴75–90%。
5. 17条run、4条responseModel、designModel、optimization、约束和区组节点均逐字节保持。未改变任何观测值、模型、拟合或寻优设置。

## 如何讲图
- 优先讲温度交互趋势图和F/P相比权衡图，3D面作为空间形状辅助。
- 相同响应在不同初始氟水平下使用相同坐标、色标与等高线；清楚区分变化幅度和颜色变化。
- 图中曲线/色面是模型条件均值预测，圆点是已测工况。模型曲线不等于独立验证结果。
- Z轴75–90%为展示该实验范围内差异所采用的截取尺度；不可把视觉坡度当作绝对效应大小。
- 初始氟0.8%或1.2%时，温度–相比矩形四角超出BBD设计点凸包，已灰显遮蔽；1.0%时整个矩形在凸包内。
- 温度和相比的影响取决于其他因素的固定值，不能把某条条件切片说成所有条件下的平均规律。
- P模型保持原项目2FI，与先前报告推荐的P线性不同；本包用于与原软件图形对应，不重新选择模型。
- β的Run6/8/9/12分别为74、133.5、113、285，与之前正式截图不同，也与当前F/P反算存在偏差。本任务保留上传项目原值，详见beta_consistency_check.csv；不据β模型宣布最优点。
- 本次没有实际能耗记录，图形不证明节能。

## 复现
安装requirements.txt中的依赖后运行：
`python build_readable_graphs.py source_project.dxpx --output regenerated`
随后运行 `python make_graph_ppt.py regenerated` 生成图版PPT。
本脚本保留原项目混合编码，仅作字节级最小修改。
