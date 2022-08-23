import argparse
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

if __name__ == "__main__":
    cfg = get_config()
    port = cast(int, cfg["site"]["backend_port"])
    parser = argparse.ArgumentParser(prog="Mystbin")
    parser.add_argument("--no-workers", "-nw", action="store_true", default=False)
    parser.add_argument("--no-cli", "-nc", action="store_true", default=False)
    parser.add_argument("--workers", "-w", nargs=1, default=os.cpu_count() or 1)

    ns = parser.parse_args(sys.argv[1:])
    
    use_workers: bool = not ns.no_workers
    use_cli: bool = not ns.no_cli
    worker_count: int = ns.workers
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
        config.workers = worker_count
        sock = config.bind_socket()

        runner = Multiprocess(config, target=server.run, sockets=[sock])
    else:
        runner = server

    try:
        runner.run()
    finally:
        if _cli_path.exists():
            os.remove(_cli_path)
