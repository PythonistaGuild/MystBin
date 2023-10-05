import json
import os

from aiohttp import web


app = web.Application()
app.config = {}
router = web.RouteTableDef()


def load_config():
    if os.path.exists("./config.json"):
        with open("./config.json", "r") as __f:
            config = json.load(__f)

    elif os.path.exists("../../config.json"):
        with open("../../config.json", "r") as __f:
            config = json.load(__f)

    else:
        raise RuntimeError("Cannot find config file")

    app.config = config


load_config()


@router.post("/reload")
async def router_reload(request: web.Request) -> web.Response:
    if (
        request.remote == "127.0.0.1" and "X-Forwarded-For" not in request.headers
    ):  # systemd reloads will only ever come from localhost using curl
        load_config()
        return web.Response(body="Reloaded", status=200)

    raise web.HTTPPermanentRedirect("/")


@router.get("/")
@router.get("/{pth:.*}")
@router.post("/")
@router.post("/{pth:.*}")
@router.patch("/")
@router.patch("/{pth:.*}")
async def fallback_route(request: web.Request) -> web.Response | web.FileResponse:
    if app.config.get("maintenance", False):  # type: ignore
        return web.FileResponse("maintenance.html")

    return web.FileResponse("service_failure.html")


app.add_routes(router)

web.run_app(app, port=app.config["site"]["fallback_port"])  # type: ignore
