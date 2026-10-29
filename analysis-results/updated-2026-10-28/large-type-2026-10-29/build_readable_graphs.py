#!/usr/bin/env python3
"""Preserve a DX13 project numerically and draw legible conditional model plots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'native_graphs_mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
import statsmodels.api as sm

LABELS = ['Temperature (°C)', 'Phase ratio', 'Initial fluoride (%)']
CENTRE = np.array([85., 1., 1.])
STEP = np.array([10., .333, .2])
TERMS = ['Intercept', 'A', 'B', 'C', 'AB', 'AC', 'BC', 'A^2', 'B^2', 'C^2']
NAVY, TEAL, ORANGE, GREY = '#15384c', '#087f8c', '#d36a27', '#586671'


def matrix(x, terms):
    a, b, c = np.atleast_2d(x).T
    all_terms = dict(zip(TERMS, [np.ones(len(a)), a, b, c, a*b, a*c, b*c, a*a, b*b, c*c]))
    return np.column_stack([all_terms[t] for t in terms])


def parse(raw):
    # Lossless one-byte decoding: the original contains both UTF-8 and GBK labels.
    root = ET.fromstring(raw.decode('latin1'))
    rows = []
    for run in root.findall('run'):
        f = {n.get('id'): float(n.text) for n in run.findall('facActual')}
        r = {n.get('id'): float(n.text) for n in run.findall('resVal')}
        rows.append(dict(Std=int(run.get('stdNo')), Run=int(run.get('runNo')),
                         Temperature=f['A'], Ratio=f['B'], Initial_F=f['C'],
                         F=r['1'], P=r['2'], beta=r['3']))
    d = pd.DataFrame(rows).sort_values('Run').reset_index(drop=True)
    coded = (d[['Temperature', 'Ratio', 'Initial_F']].to_numpy() - CENTRE) / STEP
    models = {}
    for rid, col in [('1', 'F'), ('2', 'P'), ('3', 'beta')]:
        rm = next(n for n in root.findall('responseModel')
                  if n.find('response').get('id') == rid and n.find('compModel') is not None)
        eq = [n for n in rm.findall('compModel/equationTerm') if n.get('coef') is not None]
        terms = [n.get('term') for n in eq]
        saved = np.array([float(n.get('coef')) for n in eq])
        m = sm.OLS(d[col].to_numpy(), matrix(coded, terms)).fit()
        assert np.allclose(saved, m.params, atol=1e-11, rtol=0)
        models[col] = (terms, saved, m)
    assert len(d) == 17 and len(np.unique(coded, axis=0)) == 13
    return d, models


def improve_project(raw):
    patched = raw
    factor_names = {'A': 'Temperature', 'B': 'Phase ratio', 'C': 'Initial fluoride'}
    response_names = {'1': 'Fluoride extraction', '2': 'Phosphorus extraction', '3': 'Fluoride selectivity'}
    for tag, names in [('factor', factor_names), ('response', response_names)]:
        section_name = b'factorInfo' if tag == 'factor' else b'responseInfo'
        section = re.search(b'<' + section_name + b'>.*?</' + section_name + b'>', patched, re.S).group()
        revised = section
        for ident, name in names.items():
            pattern = rb'(<'+tag.encode()+rb' id="'+ident.encode()+rb'" name=")[^"]*(")'
            revised, count = re.subn(pattern, lambda m: m[1] + name.encode() + m[2], revised)
            assert count == 1
        if tag == 'factor':
            revised = revised.replace('unit="℃"'.encode(), 'unit="°C"'.encode())
        patched = patched.replace(section, revised, 1)
    match = re.search(rb'<graphArea name="Model" index="0" graph="0">.*?</graphArea>', patched, re.S)
    section = match.group()
    revised = re.sub(rb'\r?\n<label type="factor" index="2">.*?</label>', b'', section)
    for idx in [0, 1]:
        pattern = rb'(<axis type="factor" index="'+str(idx).encode()+rb'">)(.*?)(</axis>)'
        def change_axis(m):
            body = re.sub(rb'<low>[^<]*</low>', b'<low>-1</low>', m[2])
            body = re.sub(rb'<high>[^<]*</high>', b'<high>1</high>', body)
            return m[1] + body + m[3]
        revised, count = re.subn(pattern, change_axis, revised, flags=re.S)
        assert count == 1
    # Delete oversized per-graph overrides; inherit the user's global font preferences.
    revised = re.sub(rb' fontSize="(?:44|45)"', b'', revised)
    contour_pattern = rb'(<contours type="response" index="0"[^>]*>)(.*?)(</contours>)'
    levels = b'\r\n<format>General</format>\r\n' + b''.join(
        b'<contourLevel>'+str(n).encode()+b'</contourLevel>\r\n' for n in [78, 80, 82, 84, 86, 88])
    revised, count = re.subn(contour_pattern, lambda m: m[1]+levels+m[3], revised, flags=re.S)
    assert count == 1
    patched = patched[:match.start()] + revised + patched[match.end():]
    # The numerical and fitted-model blocks are protected byte for byte.
    protected = {}
    for tag in ['run', 'responseModel', 'designModel', 'optimization', 'constraintInfo', 'blockInfo']:
        pattern = rb'<'+tag.encode()+rb'\b[^>]*(?:/>|>.*?</'+tag.encode()+rb'>)'
        before = re.findall(pattern, raw, re.S)
        after = re.findall(pattern, patched, re.S)
        assert before == after, tag
        protected[tag] = {'count': len(before), 'identical_bytes': True,
                          'sha256': hashlib.sha256(b''.join(before)).hexdigest()}
    a, b = parse(raw), parse(patched)
    pd.testing.assert_frame_equal(a[0], b[0], check_exact=True)
    for key in a[1]:
        assert np.array_equal(a[1][key][1], b[1][key][1])
    # Structural validation with lossless decoding, never rewrite the whole XML tree.
    ET.fromstring(patched.decode('latin1'))
    return patched, protected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    out = args.output
    figs = out / 'figures'
    figs.mkdir(parents=True, exist_ok=True)
    raw = args.project.read_bytes()
    d, models = parse(raw)
    patched, protected = improve_project(raw)
    (out / 'response_surface_readable.dxpx').write_bytes(patched)
    (out / 'source_project.dxpx').write_bytes(raw)
    d.to_csv(out / 'source_data.csv', index=False, float_format='%.15g')
    source_copy = out / 'build_readable_graphs.py'
    if Path(__file__).resolve() != source_copy.resolve():
        shutil.copy2(__file__, source_copy)
    plt.rcParams.update({
        'font.family': 'Liberation Serif', 'font.size': 16, 'axes.labelsize': 18,
        'axes.titlesize': 19, 'xtick.labelsize': 14, 'ytick.labelsize': 14,
        'legend.fontsize': 13, 'axes.unicode_minus': False,
        'axes.spines.top': False, 'axes.spines.right': False,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.dpi': 240,
    })
    v = np.linspace(-1, 1, 121)
    aa, bb = np.meshgrid(v, v)
    tt, rr = 85+10*aa, 1+.333*bb
    manifest = []
    pdf = PdfPages(out / 'readable_graphs.pdf')

    def prediction(col, xyz):
        terms, coef, _ = models[col]
        return matrix(xyz, terms) @ coef

    def field(col, c):
        points = np.column_stack([aa.ravel(), bb.ravel(), np.full(aa.size, c)])
        z = prediction(col, points).reshape(aa.shape)
        mask = np.abs(aa)+np.abs(bb)+abs(c) > 2+1e-10
        return np.ma.array(z, mask=mask)

    def axes_style(ax):
        ax.set(xlabel=LABELS[0], ylabel=LABELS[1], xlim=(75, 95), ylim=(.667, 1.333))
        ax.set_xticks([75, 80, 85, 90, 95])
        ax.set_yticks([.667, 1, 1.333], ['0.667', '1.000', '1.333'])
        ax.set_facecolor('#edf0f2')

    def finish(fig, stem, caption):
        fig.savefig(figs / (stem+'.png'), facecolor='white')
        svg = figs / (stem+'.svg')
        fig.savefig(svg, facecolor='white')
        # Keep editable SVG text and request the user's installed Times New Roman.
        text = svg.read_text()
        text = text.replace("'Liberation Serif'", "'Times New Roman', 'Liberation Serif', serif")
        svg.write_text(text)
        pdf.savefig(fig, facecolor='white')
        plt.close(fig)
        manifest.append({'file': stem, 'caption': caption})

    for c, code in [(0., '1p0'), (-1., '0p8')]:
        z = field('F', c)
        fig = plt.figure(figsize=(15.5, 7.2))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1], left=.055, right=.945, bottom=.17, top=.84, wspace=.25)
        ax = fig.add_subplot(gs[0, 0], projection='3d')
        ax.plot_surface(tt, rr, z.filled(np.nan), cmap='viridis', norm=Normalize(75,90),
                        rcount=65, ccount=65, linewidth=.18, edgecolor='#45606a', alpha=.97)
        ax.set(xlabel=LABELS[0], ylabel=LABELS[1], zlabel='Fluoride extraction (%)',
               xlim=(75,95), ylim=(.667,1.333), zlim=(75,90))
        ax.set_xticks([75,85,95]); ax.set_yticks([.667,1,1.333]); ax.set_zticks([75,80,85,90])
        ax.tick_params(axis='x', pad=0, labelsize=13)
        ax.tick_params(axis='y', pad=10, labelsize=13)
        ax.xaxis.labelpad=10; ax.yaxis.labelpad=12; ax.zaxis.labelpad=12
        ax.view_init(elev=26, azim=-128)
        ax.set_box_aspect((1.2,1,.8))
        ax.set_title('(a) Response surface', pad=14)
        ax = fig.add_subplot(gs[0, 1])
        filled = ax.contourf(tt, rr, z, levels=np.arange(75,90.01,.25), cmap='viridis', extend='neither')
        lines = ax.contour(tt, rr, z, levels=np.arange(76,90.01,2), colors='#152e3b', linewidths=.9)
        ax.clabel(lines, fmt='%g', fontsize=13, inline=True)
        selected = d[np.isclose(d.Initial_F, 1+.2*c)]
        ax.scatter(selected.Temperature, selected.Ratio, s=45, facecolor='white', edgecolor=NAVY,
                   linewidth=1.2, clip_on=False, zorder=5)
        axes_style(ax)
        ax.set_title('(b) Contours; circles = measured settings', pad=14, fontsize=17)
        cb = fig.colorbar(filled, ax=ax, ticks=[75,80,85,90], pad=.025, fraction=.045)
        cb.set_label('Fluoride extraction (%)', fontsize=15)
        fig.suptitle(f'Fluoride extraction | Initial fluoride = {1+.2*c:.1f}%', fontsize=23, color=NAVY, y=.96)
        note = 'Saved quadratic model; vertical axis and colour scale fixed at 75–90%.'
        if c != 0: note += '\nGrey corners are outside the convex hull of the experimental settings.'
        fig.text(.5,.055,note,ha='center',fontsize=14,color=GREY)
        finish(fig, '01_F_surface_C'+code, f'初始氟含量{1+.2*c:.1f}%时，氟萃取率曲面与等高线；Z轴明确为75–90%。')

    for col, title, scale, levels in [
        ('F', 'Fluoride extraction (%)', (75,90), np.arange(76,90.01,2)),
        ('P', 'Phosphorus extraction (%)', (0,11), np.arange(0,11.01,2)),
    ]:
        fig, axs = plt.subplots(1,3,figsize=(16,6.3))
        fig.subplots_adjust(left=.065,right=.895,bottom=.22,top=.80,wspace=.17)
        for ax, c in zip(axs, [-1.,0.,1.]):
            z = field(col,c)
            filled = ax.contourf(tt,rr,z,levels=np.linspace(*scale,61),cmap='viridis')
            cs = ax.contour(tt,rr,z,levels=levels,colors='#173442',linewidths=.8)
            ax.clabel(cs,fmt='%g',fontsize=13)
            axes_style(ax)
            ax.set_xticks([75,85,95])
            ax.set_title(f'Initial fluoride = {1+.2*c:.1f}%')
            selected = d[np.isclose(d.Initial_F,1+.2*c)]
            ax.scatter(selected.Temperature,selected.Ratio,s=35,facecolor='white',edgecolor=NAVY,
                       clip_on=False,zorder=4)
        cax = fig.add_axes([.915,.22,.015,.58])
        cb = fig.colorbar(filled,cax=cax,ticks=[75,80,85,90] if col=='F' else [0,2,4,6,8,10])
        cb.set_label(title,fontsize=16)
        model_name = 'saved quadratic model' if col == 'F' else 'saved 2FI model'
        fig.suptitle(f'{title} | {model_name}',fontsize=23,color=NAVY,y=.96)
        fig.text(.5,.065,'Identical axes and colour scales across panels. Circles = measured settings.\nGrey corners = outside the experimental convex hull; coloured regions show model predictions.',
                 ha='center',fontsize=14,color=GREY)
        finish(fig, '02_'+col+'_three_conditions', '三个初始氟水平使用统一坐标和色标；灰区表示超出设计凸包。')

    fig, axs = plt.subplots(1,2,figsize=(15,6.7))
    fig.subplots_adjust(left=.075,right=.97,bottom=.22,top=.79,wspace=.24)
    colours = ['#2166ac','#087f8c','#c86625']
    for col, ax in zip(['F','P'],axs):
        for c, colour in zip([-1.,0.,1.],colours):
            xyz = np.column_stack([v,np.zeros(len(v)),np.full(len(v),c)])
            yy = prediction(col,xyz)
            ax.plot(85+10*v,yy,lw=2.8,color=colour,label=f'Initial fluoride {1+.2*c:.1f}%')
        ax.set(xlabel='Temperature (°C)',ylabel=('Fluoride' if col=='F' else 'Phosphorus')+' extraction (%)',
               xlim=(75,95),ylim=(80,90) if col=='F' else (3.8,7.1))
        ax.set_xticks([75,80,85,90,95]);ax.grid(alpha=.18)
        ax.legend(frameon=False,loc='upper left' if col=='F' else 'upper right')
        ax.set_title('(a) Fluoride: quadratic model' if col=='F' else '(b) Phosphorus: 2FI model',fontsize=19)
    fig.suptitle('Temperature response depends on initial fluoride | Phase ratio = 1.000',fontsize=23,color=NAVY,y=.96)
    fig.text(.5,.065,'Conditional mean predictions from the unchanged project models.\nThe panels use different vertical scales; slopes alone do not establish statistical significance.',
             ha='center',fontsize=14,color=GREY)
    finish(fig,'03_temperature_interaction','相比固定为1，比较三个初始氟水平下的温度响应，突出温度×初始氟交互。')

    b = np.linspace(-1,1,401)
    xyz = np.column_stack([np.zeros(len(b)),b,np.zeros(len(b))])
    ff, pp = prediction('F',xyz),prediction('P',xyz)
    fig,ax=plt.subplots(figsize=(10.5,7.3))
    fig.subplots_adjust(left=.12,right=.91,bottom=.22,top=.82)
    ax.fill_between([0,5],80,91,color='#e7f2e9',zorder=0)
    ax.axhline(80,color=GREY,ls='--',lw=1.5);ax.axvline(5,color=GREY,ls='--',lw=1.5)
    ax.plot(pp,ff,color=GREY,lw=1.8,zorder=1)
    dots=ax.scatter(pp,ff,c=1+.333*b,cmap='viridis',s=20,zorder=2)
    for ratio, offset in [(.667,(10,10)),(.830,(10,-27)),(1.,(10,-20)),(1.333,(-105,-18))]:
        pt=np.array([[0,(ratio-1)/.333,0]])
        f,p=float(prediction('F',pt)[0]),float(prediction('P',pt)[0])
        ax.scatter(p,f,s=65,facecolor='white',edgecolor=NAVY,zorder=3)
        ax.annotate(f'Ratio {ratio:.3f}',(p,f),xytext=offset,textcoords='offset points',fontsize=15)
    ax.set(xlim=(0,11),ylim=(76,91),xlabel='Phosphorus extraction (%)',ylabel='Fluoride extraction (%)')
    ax.text(.35,90,'F ≥ 80%, P ≤ 5%',color='#386b53',fontsize=17)
    ax.grid(alpha=.15)
    fig.colorbar(dots,ax=ax,pad=.025).set_label('Phase ratio')
    fig.suptitle('Increasing phase ratio: fluoride recovery and phosphorus loss',fontsize=22,color=NAVY,y=.96)
    fig.text(.5,.065,'Temperature = 85°C; initial fluoride = 1.0%. Curve = model mean predictions.\nThe shaded target region does not imply that each future experimental batch will comply.',
             ha='center',fontsize=14,color=GREY)
    finish(fig,'04_FP_phase_ratio_tradeoff','固定85°C、初始氟1%；展示相比提高时氟回收与磷损失同时增加的权衡。')
    pdf.close()

    check = d.F*(100-d.P)/(d.P*(100-d.F))
    consistency = d[['Run','beta']].copy()
    consistency['beta_calculated_from_current_F_P'] = check
    consistency['relative_difference_percent'] = 100*(d.beta/check-1)
    consistency.to_csv(out/'beta_consistency_check.csv',index=False,float_format='%.12g')
    metrics = {}
    for col,(terms,coef,m) in models.items():
        h=m.get_influence().hat_matrix_diag
        metrics[col]={'terms':terms,'coefficients':coef.tolist(),'R2':m.rsquared,
                      'adjusted_R2':m.rsquared_adj,'predicted_R2':1-np.sum((m.resid/(1-h))**2)/m.centered_tss}
    audit={'source_sha256':hashlib.sha256(raw).hexdigest(),
           'modified_sha256':hashlib.sha256(patched).hexdigest(),
           'protected_sections':protected,'data_exactly_unchanged':True,'saved_models_exactly_unchanged':True,
           'native_application_open_test':False,
           'native_changes':['English factor/response names; units unchanged semantically',
                             'F graph factor axes restored to coded [-1,1]',
                             'Removed erroneous custom label and oversized legend font overrides',
                             'Refreshed auto-contour cached levels; retained C=0.8% and 3D graph method'],
           'models':metrics,'figures':manifest,
           'png_pdf_font':'Liberation Serif (Times New Roman not installed in this environment)',
           'svg_font_request':'Times New Roman, Liberation Serif, serif; editable text'}
    (out/'verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    pd.DataFrame(manifest).to_csv(out/'figure_index.csv',index=False,encoding='utf-8-sig')
    readme='''# 响应面图：突出条件变化规律

依据用户上传的 Design-Expert 13 原项目完整精度数据及其保存模型绘制。F使用完整二次；P使用原项目2FI；β不绘制可靠优化曲面。原文件、改图副本、源数据及验证记录均在包内。

## 使用文件
- `response_surface_readable.dxpx`：恢复显示范围和英文名称的项目副本。保留原固定初始氟含量0.8%。请用Design-Expert 13打开；本环境无法进行原软件试开验证。
- `readable_graphs.pdf`：6页图，已实际渲染检查。
- `figures/*.png`：适合PPT的高清图片。
- `figures/*.svg`：可编辑文字的矢量图，字体请求为Times New Roman；本机缺少该字体，PNG/PDF预览使用Liberation Serif替代。不能将预览称为真正的新罗马字体。
- `source_data.csv`、`source_project.dxpx`：本次来源数据及原项目。
- `verification.json`：逐字节保护校验、模型项、统计值及图形清单。
- `readable_graphs.pptx`：6页图版，供插入原组会PPT使用；中文标题与说明可编辑。

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
'''
    (out/'README.md').write_text(readme)
    (out/'requirements.txt').write_text('numpy\npandas\nscipy\nstatsmodels\nmatplotlib\n')
    print(json.dumps({'output':str(out),'figures':len(manifest),'protected':protected},ensure_ascii=False))


if __name__=='__main__':
    main()
