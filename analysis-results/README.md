# 响应面实验分析结果

根据用户提供的“响应面实验处理.xlsx”，以用户确认的 **Sheet1** 为唯一正式数据源，分析17次三因素 Box–Behnken 实验。优化目标为兼顾提高氟萃取率和降低磷损失率。

## 文件下载

- [完整文件包 ZIP（约5 MB）](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/response_surface_results.zip)
- [结果工作簿 Excel](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/response_surface_results.xlsx)
- [中文分析报告 HTML](https://github.com/zjh-1206/-/raw/refs/heads/main/analysis-results/response_surface_report.html)
- [SHA256 校验值](SHA256SUMS.txt)

HTML 报告请下载后用浏览器打开，图表已经嵌入，可离线阅读。若直接下载链接未打开，可进入对应文件页面，使用 GitHub 的 **Download raw file** 按钮。私有仓库需要先登录有访问权限的 GitHub 账号。

完整文件包包含报告、16页结果工作簿、六张诊断/响应面/权衡图、可导入的数据 CSV、Python 分析脚本、依赖版本及未经修改的原始工作簿副本。

## 主要结果

- 按氟萃取率与磷损失率的等权期望度比较，现有实测中的运行9表现最好：温度95、相比1、初始氟含量1.2，氟萃取率86.19%，磷损失率4.30%。条件单位沿用原表；原表未注明的单位未擅自补充。
- 氟萃取率完整二次模型：R²=0.9807，留一预测R²=0.7402。磷损失率线性模型的留一预测R²为0.6729，优于完整二次模型。
- 氟选择性系数β模型失拟显著，不用于可靠预测或寻优。
- 运行8对磷线性模型影响明显，应核查原始实验记录；主分析保留全部17次运行，未删点或修改测量值。
- 模型探索候选为温度95、相比0.976、初始氟含量1.108，预测氟萃取率约85.25%、磷损失率约4.96%。该位置对数据与模型形式敏感，不能认定优于运行9，需与运行9并行开展独立重复验证。

计算使用 Python 常规响应面统计方法，未运行专有 Design-Expert 软件。CSV 可手动映射因素与响应后导入；此处不包含该软件的原生项目文件。所有体积与浓度计算沿用原表公式及报告明确列出的假设。
