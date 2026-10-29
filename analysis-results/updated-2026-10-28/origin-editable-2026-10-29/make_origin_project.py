#!/usr/bin/env python3
"""Run in Origin 2021+ Code Builder (F5) to create editable native graphs.

This is a project *generator*, not a pre-generated or validated OPJU file.
An offline --check-only mode verifies the supplied numeric data without Origin.
"""
from pathlib import Path
from datetime import datetime
import csv
import hashlib
import json
import sys
import traceback
import numpy as np

ROOT = Path(__file__).resolve().parent
LOG = []
GRAPH_PAGES = []


def log(message):
    LOG.append(str(message))
    print(message)


def read_csv(name):
    with (ROOT / name).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        heads = reader.fieldnames
        rows = list(reader)
    return heads, {h: [float(r[h]) for r in rows] for h in heads}


def validate_data():
    recipe = json.loads((ROOT / 'plot_recipe.json').read_text(encoding='utf-8'))
    with np.load(ROOT / 'matrix_data.npz', allow_pickle=False) as z:
        assert np.allclose(z['temperature'], np.linspace(75, 95, 81))
        assert np.allclose(z['phase_ratio'], np.linspace(.667, 1.333, 81))
        for info in recipe['matrices']:
            matrix = z[info['key']]
            assert matrix.shape == (81, 81)
            a, b = np.meshgrid(np.linspace(-1, 1, 81), np.linspace(-1, 1, 81))
            outside = np.abs(a) + np.abs(b) + abs(info['coded_C']) > 2 + 1e-10
            assert np.array_equal(np.isnan(matrix), outside)
            assert np.isfinite(matrix[~outside]).all()
    for name, expected in recipe['input_sha256'].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, 'Data checksum mismatch: ' + name
    _, original = read_csv('source_data.csv')
    assert len(original['Run']) == 17
    log('Data check passed: 17 observations; 6 matrices; hull masking; file checksums.')
    return recipe


def optional(action, description):
    try:
        return action()
    except Exception as exc:
        log('STYLE/EXPORT NOTE: ' + description + ': ' + str(exc))
        return None


def verified_numeric_property(obj, prop, target):
    """Version-sensitive properties are read back, never declared successful blindly."""
    obj.set_float(prop, target)
    actual = obj.get_float(prop)
    if not np.isfinite(actual) or abs(actual-target) > .1:
        raise RuntimeError('%s did not confirm %s; read back %s' % (prop, target, actual))


def set_title(gl, axis, text):
    gl.axis(axis).title = text
    label_name = {'x': 'xb', 'y': 'yl', 'z': 'zb'}[axis]
    label = gl.label(label_name)
    if label is not None:
        label.set_int('fsize', 28)
        optional(lambda: gl.lt_exec('%s.font=font("Times New Roman");' % label_name),
                 label_name + ' font family; verify in Origin')


def style(gl, x_title, y_title, z_title=None):
    set_title(gl, 'x', x_title)
    set_title(gl, 'y', y_title)
    if z_title:
        set_title(gl, 'z', z_title)
    # These LabTalk tick-font properties vary between versions. Failure does not
    # compromise data or native editability and is recorded in origin_build_log.txt.
    for axis in ('x', 'y', 'z') if z_title else ('x', 'y'):
        optional(lambda axis=axis: verified_numeric_property(gl, axis+'.label.pt', 24),
                 axis + ' tick font size')
    for name in ['Legend', 'ColorScale']:
        label = gl.label(name)
        if label is not None:
            optional(lambda label=label: label.set_int('fsize', 24), name + ' font size')


def set_palette(plot, recipe):
    # Maple.pal is used in the verified OriginLab example. Its appearance must
    # still be compared with the supplied reference RGB swatches on the local PC.
    name = recipe.get('origin_palette', 'Maple.pal')
    optional(lambda: setattr(plot, 'colormap', name), 'Origin palette ' + name)


def workbook(op, csv_name, long_name, x_col=None):
    heads, columns = read_csv(csv_name)
    w = op.new_sheet('w', lname=long_name)
    if w is None:
        raise RuntimeError('Could not create native worksheet: ' + long_name)
    for i, h in enumerate(heads):
        kwargs = {'lname': h}
        if x_col is not None:
            kwargs['axis'] = 'X' if i == x_col else 'Y'
        w.from_list(i, columns[h], **kwargs)
    return w


def register(graph, title, generated):
    if graph is None:
        raise RuntimeError('Origin graph creation failed: ' + title)
    GRAPH_PAGES.append(graph)
    log('Native graph created: ' + title)
    # PNG exports are secondary previews; graphs themselves remain native objects.
    optional(lambda: graph.save_fig(str(generated / (graph.name+'.png')), width=2400),
             'export preview: ' + title)


def create_project(recipe):
    import originpro as op
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    generated = ROOT / ('generated_in_origin_' + stamp)
    generated.mkdir()
    project_path = generated / 'response_surface_editable.opju'
    # Deliberately do not call op.new(): the default would discard unsaved work.
    # Start with an empty project yourself; existing windows are never deleted here.
    log('Output folder: ' + str(generated))
    original = workbook(op, 'source_data.csv', 'RSM original 17 runs')
    original.comments = 'Full precision from supplied DX13 project; observed data unchanged.'
    notes = op.new_notes('RSMReadMe')
    if notes is not None:
        optional(lambda: setattr(notes, 'text',
            'F quadratic; P 2FI from the uploaded DX13 project. Curves and surfaces are model mean predictions. '
            'Blank matrix corners are outside the BBD hull. Beta values are retained, not used to claim a reliable optimum. '
            'Font settings and rendering must be checked in this local Origin installation.'), 'project notes')
    matrices = {}
    failures = []
    with np.load(ROOT / 'matrix_data.npz', allow_pickle=False) as packed:
        for info in recipe['matrices']:
            key = info['key']
            ms = op.new_sheet('m', lname=key)
            if ms is None:
                raise RuntimeError('Could not create native matrix ' + key)
            ms.from_np(np.asarray(packed[key], dtype=np.float64))
            ms.xymap = (75, 95, .667, 1.333)
            ms.set_label(0, info['description'])
            ms.set_label('x', 'Temperature (°C)')
            ms.set_label('y', 'Phase ratio')
            ms.comments = info['description']
            matrices[key] = ms
            try:
                g = op.new_graph(lname=info['description'], template='contour')
                if g is None: raise RuntimeError('Built-in contour template not found')
                gl = g[0]
                p = gl.add_mplot(ms, z=0, type='contour')
                if p is None: raise RuntimeError('Matrix contour plot failed')
                gl.rescale()
                p.zlevels = {'levels': info['levels'], 'minors': 4}
                set_palette(p, recipe)
                gl.set_xlim(75, 95, 5)
                gl.set_ylim(.667, 1.333, .111)
                style(gl, 'Temperature (°C)', 'Phase ratio')
                legend = gl.label('Legend')
                if legend is not None:
                    legend.text = info['description']
                    legend.set_int('fsize', 24)
                register(g, info['description'], generated)
            except Exception as exc:
                failures.append(key + ': ' + str(exc))
                log('GRAPH ERROR: ' + failures[-1])
        for key in ['F_C1p0', 'F_C0p8']:
            try:
                g = op.new_graph(lname=key+' surface', template='glCMAP')
                if g is None: raise RuntimeError('Built-in glCMAP template not found')
                gl = g[0]
                p = gl.add_mplot(matrices[key], z=0, type=103)
                if p is None: raise RuntimeError('Matrix surface plot failed')
                gl.rescale()
                set_palette(p, recipe)
                p.zlevels = {'levels': [75, 78, 80, 82, 84, 86, 88, 90], 'minors': 4}
                gl.set_xlim(75, 95, 5); gl.set_ylim(.667, 1.333); gl.set_zlim(75, 90, 5)
                style(gl, 'Temperature (°C)', 'Phase ratio', 'F extraction (%)')
                register(g, key+' surface', generated)
            except Exception as exc:
                failures.append(key+' surface: '+str(exc));log('GRAPH ERROR: '+failures[-1])

    trend = workbook(op, 'temperature_trends.csv', 'RSM temperature predictions', x_col=0)
    colours = ['#2166ac', '#087f8c', '#c86625']
    for response, columns, ylim in [('F', [1, 2, 3], (80,90,2)), ('P', [4,5,6], (4,7.2,.5))]:
        try:
            g=op.new_graph(lname=response+' temperature response, ratio=1', template='line')
            if g is None: raise RuntimeError('Built-in line template not found')
            gl=g[0]
            for col, colour in zip(columns, colours):
                plot=gl.add_plot(trend, coly=col, colx=0, type='line')
                if plot is None: raise RuntimeError('Native line plot failed')
                plot.color=colour
                optional(lambda plot=plot: plot.set_cmd('-w 3'), 'line width')
            gl.rescale();gl.set_xlim(75,95,5);gl.set_ylim(*ylim)
            style(gl, 'Temperature (°C)', response+' extraction (%)')
            legend=gl.label('Legend')
            if legend is not None:
                legend.text='Initial fluoride\n\\l(1) 0.8%\n\\l(2) 1.0%\n\\l(3) 1.2%'
                legend.set_int('fsize',24)
            register(g, response+' temperature response', generated)
        except Exception as exc:
            failures.append(response+' trend: '+str(exc));log('GRAPH ERROR: '+failures[-1])

    trade=workbook(op,'phase_ratio_tradeoff.csv','RSM phase-ratio predictions')
    try:
        g=op.new_graph(lname='F-P tradeoff: T=85 C=1%',template='line');gl=g[0]
        p=gl.add_plot(trade,coly=2,colx=1,type='line')
        if p is None: raise RuntimeError('Native tradeoff line failed')
        p.color='#087f8c'
        gl.rescale();gl.set_xlim(0,11,2);gl.set_ylim(76,91,2)
        style(gl,'P extraction (%)','F extraction (%)')
        for coords in [(0,80,11,80),(5,76,5,91)]:
            line=gl.add_line(*coords)
            if line is not None: line.width=1.5
        legend=gl.label('Legend')
        if legend is not None:
            legend.text='T=85°C; initial F=1.0%\nCurve: varying phase ratio\nTargets: F>=80%, P<=5%'
            legend.set_int('fsize',24)
        register(g,'F-P phase-ratio tradeoff',generated)
    except Exception as exc:
        failures.append('tradeoff: '+str(exc));log('GRAPH ERROR: '+failures[-1])

    if not op.save(str(project_path)):
        raise RuntimeError('Origin did not confirm saving: '+str(project_path))
    log('Saved native Origin project: '+str(project_path))
    log('Created %d/11 graph pages.' % len(GRAPH_PAGES))
    if failures:
        log('Some graph creation steps failed; matrices and successful graphs are saved. See errors above.')
    log('To keep graphs editable in PowerPoint: run copy_active_graph_to_ppt.py, then paste as an Origin object.')
    (generated/'origin_build_log.txt').write_text('\n'.join(LOG),encoding='utf-8')
    (ROOT/'LAST_OUTPUT.txt').write_text(str(project_path)+'\n',encoding='utf-8')
    return project_path, failures


def main():
    recipe=validate_data()
    if '--check-only' in sys.argv:
        return
    try:
        create_project(recipe)
    except Exception:
        text=traceback.format_exc();log(text)
        (ROOT/'origin_failed_log.txt').write_text('\n'.join(LOG),encoding='utf-8')
        raise


if __name__=='__main__':
    main()
