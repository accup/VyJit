from aiohttp import web
from aiohttp_jinja2 import render_template

import sys
import os
import importlib
import pkgutil
import traceback


routes = web.RouteTableDef()


@routes.get('/')
async def index(request: web.Request):
    import analyzers
    analyzer_names = [
        name
        for _, name, _ in pkgutil.walk_packages(analyzers.__path__)
    ]

    return render_template(
        'pages/index.html',
        request=request,
        context={
            'analyzer_names': analyzer_names,
        },
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
        '{}/index.html'.format(analyzer_name),
        request=request,
        context={
            'analyzer_name': analyzer_name
        },
    )


# static resources
if os.path.exists('analyzers'):
    routes.static('/analyzers', 'analyzers')
if os.path.exists('static'):
    routes.static('/static', 'static')
if os.path.exists('dist'):
    routes.static('/dist', 'dist')
