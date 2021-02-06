# MystBin
Easily share your code or text with syntax highlighting and themes for readability.

# A note
This is currently in development and not full software.
It is currently unsupported, running it now is at your own risk.

## Installation and setup
### Pre-requisites
- Python 3.8+
- PostgreSQL 12.0+
    - Ability to install/use the `pgcrypto` extension.

NOTE: An optional docker-compose file has been provided for Docker use.

### Setup instructions
1. Make a copy of `config-template.toml` named `config.toml` and change the values within to suit your environment.
2. Make a copy of `.env-template` as `.env` and edit to match your environment.
    3. Run `docker-compose up -d --build` to spin up the environment that is preconfigured.
4. Install Python dependencies from spec. (see `requirements.txt` or `pyproject.toml`)
5. Run the app. This will involve changing directory to `mystbin/rest/` and running the following command:


### Database
If for any reason you wish to use a non-container version of PostgreSQL, you can remove it's optional build file from your top-level `.env` file, as based on the template provided. Just ensure your config is correct.

```sh
python -m uvicorn main:app # --host 127.0.01 --port 8000
```
You can uncomment the rest of the line to edit the default values.