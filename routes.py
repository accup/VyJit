from aiohttp import web
from aiohttp_jinja2 import render_template


routes = web.RouteTableDef()


@routes.get('/')
async def index(request: web.Request):
    return render_template(
        'pages/index.html',
        request=request,
        context=None,
    )


@routes.get('/analyzer/{analysis_name}')
async def analysis(request: web.Request):
    analysis_name = request.match_info['analysis_name']
    return render_template(
        'pages/{}.html'.format(analysis_name),
        request=request,
        context=None,
    )


routes.static('/', '_static')
