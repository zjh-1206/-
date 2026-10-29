# Origin可编辑图生成包（Origin2021及更新版本）

## 直接下载

- [Origin生成完整包ZIP](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/origin-editable-2026-10-29/origin_editable_bundle.zip)
- [绘图数据Excel](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/origin-editable-2026-10-29/Origin_plot_data.xlsx)
- [配色对比预览](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/updated-2026-10-28/origin-editable-2026-10-29/colour_comparison.png)

本包提供完整数据和在你本机Origin中生成原生图的脚本。**本环境没有Origin，尚未生成或试开OPJU；不把图片、Excel或脚本冒充已完成的Origin项目。**

## 运行（首次一次）
1. 下载ZIP并解压到一个普通本地文件夹，例如 `D:\Origin_RSM`。保持全部文件的位置关系。
2. 在Origin中保存正在处理的工作，再新建空白项目。
3. 打开Origin的 **Code Builder**，从其 **File** 菜单打开 `make_origin_project.py`，按 **F5**。这个入口依据OriginLab官方Python示例README核实。
4. 脚本创建6张等高线、2张氟曲面、2张温度趋势和1张F/P权衡图，并保存到包目录下 `generated_in_origin_时间戳/response_surface_editable.opju`。
5. `LAST_OUTPUT.txt`记录项目路径，运行目录内的`origin_build_log.txt`记录实际成功/失败步骤。若部分图失败，成功图和矩阵仍保存；请以日志为准，不假定11张全部完成。

## 在PPT里继续编辑
1. 在Origin激活要复制的图。
2. 同样在Code Builder中运行 `copy_active_graph_to_ppt.py`（F5）。脚本调用已核实的 `copy_page('OLE')`。
3. 回到PPT，使用“选择性粘贴”，选择 **Origin图形对象**（具体名称随本机版本变化）。
4. 以后双击PPT内的对象，即可调用本机Origin编辑。若粘贴成PNG/EMF，不能通过双击恢复Origin原生数据关系。运行编辑需要本机安装Origin。

## 文件与可编辑性
- `Origin_plot_data.xlsx`：17组原始实验、模型系数、6个XYZ网格和条件趋势表，可手动导入Origin。
- `matrix_data.npz`：6个81×81原生矩阵的生成数据；NaN为设计凸包外区域，不填0、不当新实验。
- `matrix_csv/`：相同矩阵的CSV备用数据。列从左到右温度75–95°C；行从上到下相比0.667–1.333。手动导入矩阵后必须设置X/Y映射。
- `source_data.csv`：上传原项目的完整精度数据；原β照原项目保留，未按F/P覆盖。
- `saved_models.json`：原项目保存系数。F完整二次、P 2FI，未重新选模或拟合。
- `temperature_trends.csv`：相比1，初始氟0.8/1/1.2%，温度75–95°C。
- `phase_ratio_tradeoff.csv`：85°C、初始氟1%，相比0.667–1.333。
- `make_origin_project.py`：创建真正Origin工作簿、矩阵、图层和曲线，并保存OPJU的生成器。
- `copy_active_graph_to_ppt.py`：把活动图复制为原生Origin OLE对象。

OPJU生成后，双击坐标改范围、字体、字号；双击曲线/等高线打开图形属性；在矩阵和工作表中编辑绘图数据。修改模型系数需重新计算网格（只编辑颜色或字体不需重新计算数据）。此包不包含自动在Origin中重新拟合模型的分析操作。

## 配色

上一版viridis配色由助手自行选择，不对应具体论文。本包根据用户提供文献图的可见顺序给出蓝→青→绿→黄→橙→红参考RGB表和预览；原生脚本采用官方例证Maple.pal，实际外观需在本机核对后按RGB表调整。详见colour_reference.md。

## 字体和显示检查
脚本用已核实的Label API把轴标题设为28、图例24。刻度LabTalk属性尝试设24并读回核验，版本不接受时记日志；字体族尝试Times New Roman，须在本机图形窗口确认。不能声称本环境已验证字体、等高线数字、色标或三维视角效果。请在Origin核对所有主要文字约24pt、固定C水平与统一色标，随后导出或复制到PPT。

## 数据解释
图形色面与曲线是原模型的条件均值预测，未增加实验；F二次/P 2FI与上传项目对应。不同固定C使用相同坐标和色标。C=0.8/1.2%时矩形角区超出BBD设计凸包，矩阵中留缺失。请核对Origin实际如何呈现这些NaN角区，避免软件自动插值填满。F/P达标线表示均值目标，不能保证每批达标。无实测能耗，未声称节能。

## 核实与限制
已核实OriginLab官方Python示例和originpro包源码；本环境可检验数字、矩阵维度、缺失区域、脚本语法和API签名，不能原生运行Origin。来源见`API_sources.md`。脚本不清空现有项目，不覆盖既有输出；仍建议先打开空白项目以便结果独立保存。

离线校验：`python make_origin_project.py --check-only`（仅需numpy，不调用Origin）。
