# 实际核实的Origin API来源

- OriginLab官方示例：https://github.com/originlab/Python-Samples ，本轮实际读取commit `9d2907866a74c7791b4ad63c6de512ab5793ed1e`。
- `README.md`：Code Builder → File打开Python文件 → F5运行。
- `4. Graphing/Plot Contour and 3D Surface Graph.py`：3D模板glCMAP、type103；XYZ等高线TriContour/type243。
- `4. Graphing/Control Plots As Group.py`：原生图层绘图、Legend.set_int('fsize',22)。
- 本轮实际下载PyPI官方originpro1.1.15源码：https://pypi.org/project/originpro/1.1.15/ 。未在本机安装并连接Origin。
- `matrix.py`：MSheet.from_np、xymap=(x1,x2,y1,y2)，float64 NaN矩阵。
- `graph.py`：zlevels示例使用contour模板和add_mplot(type='contour')；add_mplot默认103为曲面；copy_page('OLE')原生复制；GPage.save_fig导出预览。
- `project.py`：save(path)返回bool，创建工作簿/图形的new_sheet/new_graph。

本轮只核实源码和数据，没有运行Origin、保存OPJU或生成含Origin OLE对象的PPT。具体字体属性跨版本可能不同，脚本中仅作可读回检查的尽力设置并记录失败，不将其当成已验证的软件输出。
