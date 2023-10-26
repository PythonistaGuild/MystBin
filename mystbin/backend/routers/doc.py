"""Copyright(C) 2020-present PythonistaGuild

This file is part of MystBin.

MystBin is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MystBin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MystBin.  If not, see <https://www.gnu.org/licenses/>.
"""

from mystbin_models import MystbinRequest
from utils import openapi
from utils.responses import Response, UJSONResponse
from utils.router import Router
from utils.version import VERSION


html = """
<!DOCTYPE html>
<html>
<head>
<title>MystBin API</title>
<!-- needed for adaptive design -->
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">

<link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">

<!--<link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png"> -->
<!--
ReDoc doesn't change outer page styles
-->
<style>
  body {{
    margin: 0;
    padding: 0;
  }}
</style>
</head>
<body>
<redoc spec-url="{spec}"></redoc>
<script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"> </script>
</body>
</html>
"""

description = """
The following are valid values in the `Accept` Header for all endpoints that return application/json in the example.
- `application/json`
- `application/yaml`
- `application/toml`
- `application/msgpack`

Note that toml does not have NULL values, so `"NULL"` will be sent to represent them.

Ratelimits fall under two types. The global ratelimit applies to all requests, and the zone ratelimit applies to the zone of the route you're requesting.
You'll find the following headers for a typical request where both apply (the global ratelimit looks like `X-Global-Ratelimit-Foobar`):

- `X-Ratelimit-Used` - How many requests have been applied against the current ratelimit.
- `X-Ratelimit-Reset` - When the ratelimit will reset. Only applies when the strategy is `window`.
- `X-Ratelimit-Max` - The max amount of requests that can be made.
- `X-Ratelimit-Available` - How many requests are available to be made.

The following key will be available all the time:
- `X-Ratelimit-Strategy` - The method that the server is using to manage ratelimits.

The following keys will only be available for zone ratelimits (not global ones, or when there is no zone):
- `X-Ratelimit-Base-Zone` - The base zone of the request. This is static per-route. Ex `postpastes`.
- `X-Ratelimit-True-Zone` - The zone for this particular request. This can change depending on factors such as passing a valid token, Ex `authed_postpastes`.
"""

router = Router()


@router.get("/docs")
async def get_docs(_) -> Response:
    return Response(html.format(spec="/openapi.json"), media_type="text/html")


@router.get("/admindocs")
async def get_admin_docs(_) -> Response:
    return Response(html.format(spec="/admin-openapi.json"), media_type="text/html")


@router.get("/openapi.json")
async def get_openapi(request: MystbinRequest) -> UJSONResponse:
    spec = getattr(request.app.state, "openapi", None)
    if spec is None:
        request.app.state.openapi = openapi.instance.render_spec(
            "Mystbin", f"Documentation pertaining to the public useable endpoints.\n{description}", VERSION, True
        )

    return UJSONResponse(request.app.state.openapi)


@router.get("/admin-openapi.json")
async def get_admin_openapi(request: MystbinRequest) -> UJSONResponse:
    spec = getattr(request.app.state, "admin_openapi", None)
    if spec is None:
        request.app.state.admin_openapi = openapi.instance.render_spec(
            "Mystbin",
            f"Documentation pertaining to the ALL useable endpoints (including admin endpoints)\n{description}",
            VERSION,
            False,
        )

    return UJSONResponse(request.app.state.admin_openapi)
