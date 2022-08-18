import json
import os
import pathlib
import sys
from typing import cast

import uvicorn
from uvicorn.supervisors import Multiprocess


def get_config() -> dict[str, dict[str, int | str]]:
    pth = pathlib.Path("config.json")

    if not pth.exists():
        pth = pathlib.Path("../../config.json")

    if not pth.exists():
        raise RuntimeError(
            "No config.json was found. Please make sure you've copied the config-template.json into config.json and filled out the appropriate vallues"
        )

    with pth.open() as f:
        data = json.load(f)

    return data


async def run_cli():
    pass


def run_cli_with_workers():
    pass


if __name__ == "__main__":
    cfg = get_config()
    port = cast(int, cfg["site"]["backend_port"])
    use_workers = "--no-workers" not in sys.argv and cfg["redis"]["use-redis"]
    use_cli = "--no-cli" not in sys.argv
    _cli_path = pathlib.Path(".nocli")

    if not use_cli:
        with _cli_path.open("w") as f:
            f.truncate()
            f.flush()
    else:
        if _cli_path.exists():
            os.remove(_cli_path)

    if os.environ.get("ISDOCKER") is not None:
        config = uvicorn.Config("app:app", port=port, host="0.0.0.0")
        # allow from all hosts when in a docker container, so that requests can be proxied in
    else:
        config = uvicorn.Config("app:app", port=port, host="127.0.0.1")

    server = uvicorn.Server(config)

    if use_workers:
        config.workers = os.cpu_count() or 1
        sock = config.bind_socket()

        runner = Multiprocess(config, target=server.run, sockets=[sock])
    else:
        runner = server

    try:
        runner.run()
    finally:
        if _cli_path.exists():
            os.remove(_cli_path)
