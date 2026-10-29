"""Run inside Origin, with a graph active; paste into PPT as an Origin object."""
from pathlib import Path
import site
import sys
local = Path(__file__).resolve().parent / '_origin_python' / ('py%d%d' % sys.version_info[:2])
if local.exists():
    site.addsitedir(str(local))
    sys.path.insert(0, str(local))
import originpro as op
graph = op.find_graph()
if graph is None:
    raise RuntimeError('Activate an Origin graph window, then run this script again.')
graph.copy_page('OLE')
print('Origin graph copied as OLE. In PowerPoint, paste as an Origin graph object.')
print('Double-clicking the embedded object later opens Origin for editing.')
