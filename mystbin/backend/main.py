from __future__ import annotations

import asyncio
import argparse
import json
import os
import pathlib
import sys
import atexit

import uvicorn
from uvicorn.supervisors import Multiprocess

from daemon import tasks

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


def print_ignore_shutdown():
    print("\033[31;1;4mTHESE ARE EXPECTED ERRORS AND SHOULD BE IGNORED. DO NOT OPEN BUG REPORTS ABOUT THEM.\033[0m", flush=True)


if __name__ == "__main__":
    cfg = get_config()
    port: int = cfg["site"]["backend_port"]  # type: ignore # resolved when typed dict
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
    taskmaster = tasks.TaskProcessor(cfg)

    if use_workers:
        config.workers = worker_count
        sock = config.bind_socket()

        runner = Multiprocess(config, target=server.run, sockets=[sock])

        async def _run():
            await taskmaster.start()
            await asyncio.get_running_loop().run_in_executor(None, runner.should_exit.wait)
            runner.shutdown()

        def run():
            runner.startup()
            asyncio.run(_run())

    else:
        runner = server

        async def _run():
            await taskmaster.start()
            try:
                await runner.serve()
            except KeyboardInterrupt:
                pass
        
        def run():
            runner.config.setup_event_loop()
            asyncio.run(_run())
            
    try:
        atexit.register(print_ignore_shutdown) # this is stupid, but the only way to ensure the print happens after all the errors

        run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        if _cli_path.exists():
            os.remove(_cli_path)
