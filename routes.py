from aiohttp import web
from aiohttp_jinja2 import render_template
import analyzers


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
    if analyzer_name not in analyzers.SUBMODULES:
        raise web.HTTPNotFound()

    return render_template(
        'analyzers/{}.html'.format(analyzer_name),
        request=request,
        context={
            'analyzer_name': analyzer_name
        },
    )


routes.static('/', '_static')
