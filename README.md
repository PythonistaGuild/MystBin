# MystBin

Easily share code and text.


[Staging Website](https://staging.mystb.in)


### Running Locally
**Requirements:**
- Postgres

**Setup:**
- Clone
- Copy `config.template.toml` into `config.toml`
 - For local testing `[SERVER] > domain` can be set to `http://localhost:PORT` (Default Port `8181`)
 - Set Database connection DSN.
 - Optionally set URLs to a running Redis Instance.
- ! If you haven't already: Create a Database in `postgres` (Default `mystbin`)
- Install dependencies (Preferably to a `venv`): `pip install -Ur requirements.txt`
- Optionally in `core/server.py` set `ignore_localhost=` to `False` in the RateLimit Middleware for testing.
- Run: `python launcher.py`
