from aiohttp import web
from aiohttp_jinja2 import render_template

import sys
import importlib
import traceback


routes = web.RouteTableDef()


@routes.get('/')
async def index(request: web.Request):
    return render_template(
        'pages/index.html',
        request=request,
        context=None,
    )


@routes.get('/analyzers/{analyzer_name}')
async def analysis(request: web.Request):
    analyzer_name = request.match_info['analyzer_name']
    module_name = 'analyzers.{}'.format(analyzer_name)
    try:
        if module_name in sys.modules:
            module = importlib.import_module(module_name)
            importlib.reload(module)
        else:
            module = importlib.import_module(module_name)
    except Exception:
        raise web.HTTPInternalServerError(text=traceback.format_exc())

    return render_template(
        'analyzers/{}.html'.format(analyzer_name),
        request=request,
        context={
            'analyzer_name': analyzer_name
        },
    )


# Keep this order
routes.static('/socket.io', 'node_modules/socket.io-client/dist')
routes.static('/bootstrap', 'node_modules/bootstrap/dist')
routes.static('/', '_static')
