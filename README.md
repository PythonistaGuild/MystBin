# MystBin
Easily share your code or text with syntax highlighting and themes for readability.

# A note
This is currently in development and not full software.
It is currently unsupported, running it now is at your own risk.

## Installation and setup
### Pre-requisites
- Python 3.8+
- PostgreSQL 9.0+
    - Ability to install/use the `pgcrypto` extension.

### Setup instructions
1. Make a copy of `config-template.toml` named `config.toml` and change the values within to suit your environment.
2. Ensure database is ready in terms of user, login and permissions. We create the tables on launch if they do not exist already.
3. Install Python dependencies from spec. (see `requirements.txt` or `pyproject.toml`)
4. Run the app. This will involve changing directory to `mystbin/rest/` and running the following command:
```sh
python -m uvicorn main:app # --host 127.0.01 --port 8000
```
You can uncomment the rest of the line to edit the default values.