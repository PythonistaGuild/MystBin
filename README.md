<div align="center">
    <img width="320" src="res/mystbin_logo_light_full.svg", alt="Mystbin Logo"/>
    <hr>
    <p>Easily share your code or text with syntax highlighting and themes for readability.</p>
    <br>
    <p>The stable release of this can be found at <a href="https://mystb.in">mystb.in</a></p>
    <br>
    <p>The unstable version (up to date with the master branch) of this can be found at <a href="https://beta.mystb.in">beta.mystb.in</a></p>
    <br>
    <a href="https://www.python.org">
        <img src="https://img.shields.io/badge/Python-3.8%20%7C%203.9-blue.svg" />
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" />
    </a>
    <a href="https://discord.gg/RAKc3HF">
        <img src="https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white" alt="Discord Server" />
    </a>
</div>
<div align="center">
    <a href="https://github.com/PythonistaGuild/actions?query=workflow%3AAnalyze">
        <img src="https://github.com/PythonistaGuild/MystBin/workflows/Analyze/badge.svg" />
    </a>
    <a href="https://github.com/PythonistaGuild/MystBin/actions?query=workflow%3A%22Lint+Code+Base%22">
        <img src="https://github.com/PythonistaGuild/MystBin/workflows/Lint%20Code%20Base/badge.svg" />
    </a>
</div>

# API Usage
The API docs are available at [api.mystb.in/docs](https://api.mystb.in/docs).
The ratelimits are decently strict when not signed in by default, you can elevate those by using an API token.
To get an API token, log in with any oauth provider and enter the dashboard. Copy your API token into the `Authorization` header.

# Migrating
If you are migrating from V3 to V4, you'll need to follow the following steps:
- `git fetch && git checkout <v4 unified branch here>`
- `psql -d (your db name) -f mystbin/database/migrate_v4.sql`

It is important to note that this will invalidate all tokens.

### Ratelimits
The way ratelimits work differs based on whether redis is being used or not.
If redis is in use, the window method is used, where you have X requests available in a certain timeframe.
If redis is NOT in use, the leaky bucket method is used, where you gain requests after every X seconds.
The ratelimit headers will differ a slight bit depending on the method in use (ex x-ratelimit-reset is not applicable to the leaky bucket, and will always be 0).
You can always tell what method is being used via the `X-Ratelimit-Strategy` header. If this header returns `ignore`, ratelimits are not applicable to the request (ex if using an admin account).

All API responses have ratelimit information associated with them:
- `x-ratelimit-available`: How many API calls you have left before being ratelimited.
- `x-ratelimit-max`: The maximum amount of API calls you can make in a timeframe before being ratelimited.
- `x-ratelimit-reset`: When using the window method, this is a timestamp when your ratelimit will reset to full.
- `x-ratelimit-used`: "x-ratelimit-max - x-ratelimit-available", how many API calls you've made in the current window.

Alongside the above headers, there are also global ratelimits, which will return the same headers in the form of `x-global-ratelimit-(X)`


# Installation

This site requires the following external software:
- Python 3.10+
- Node.js / yarn
- postgresql 14+
- Redis (optional)

This guide assumes you are on a UNIX-ish platform (ex MacOS/Linux)

### The following instructions are for non-docker usage

## Setting up the config file
copy the config-template.json into config.json.

you'll need to change the database dsn to match your username/password/database setup.

if you wish to use redis for ratelimits, you can leave it enabled in the config. Assuming you havent changed the install at all, it should work without changes.
If you don't want to use redis, you may set use-redis to `false`, which will use in-memory ratelimits, and disable worker processes (this may degrade performance if at scale).

### Setting up apps
To use the dashboard and the API, you'll need to configure at least one of the supported oauth provider (discord, github, and google). You can do so in their developer web panels, like [discord's](https://discord.com/developers), or [github's](https://github.com/settings/developers).
After creating an app, set the callback url to `https://mysite.com/(provider)_auth`, ex `https://mystb.in/github_auth`.
You'll need to copy the client id and client secret into the config where appropriate.

You may set up the github bot token with a [github personal access token](https://github.com/settings/tokens) to enable automatic invalidation of discord tokens (via posting them in gists). You'll need the `gist` scope to allow creating gists.

### Setting up sites
The `sites` fields are used to set up CORS, and to direct the frontend to the correct location when making requests to the backend.
Setting these fields up incorrectly will lead to your frontend not being able to communicate with the backend.
the `port` settings will tell the apps what ports to run on (currently only the backend port setting is actually effective).

### Setting up Sentry
You may wish to use sentry to provide error tracking, you can do so by creating a sentry app, and inserting it's ingest url into the respective config slot.
Leaving the ingest url blank will disable sentry error tracking.

If you wish to have a webhook in discord update you on errors, simply configure a webhook to `https://mysite.com/callbacks/sentry` and insert a discord webhook url into the respective config slot.

### setting up everything else
The debug parameters can be ignored unless you're actively developing, in which case set both to `true`.

The `paste` fields give you control over how large the pastes can get, you cannot set these fields to `null`.

The `ratelimits` fields give you control over what user groups have what kinds of ratelimits. Ratelimits are formatted as `rate/per`, ex `5/minute` or `1/hour`.


## Setting up the database
**Do this before running the backend**.

After installing postgresql, you'll need to create a user and database for mystbin. Please use google for assistance on this.
After creating the database, import the schema with `psql -d (database) -f mystbin/database/schema.sql`, replacing (database) with the name of the database.
You might need to specify the user with the -u flag.

## Setting up the backend
To set up the backend, you'll want to cd into the `./mystbin/backend/` folder, and create a python venv. This can be accomplished with `python -m venv venv`. Make sure you're using python 3.8 +.
After creating the venv, activate it with `. ./venv/bin/activate`. Then you can proceed to install the dependancies by running `pip install -r requirements.txt`.

Once the dependancies are installed, you should be able to bring the backend online with `python main.py`.


## Setting up the frontend
To set up the frontend, you'll want to cd into the `./mystbin/frontend/` folder. Then, install the dependancies using yarn: `yarn install`.

You'll need to copy the config file to the frontend folder (symlinks are OK!).

After installing the dependancies and copying/symlinking the config, you can bring up the frontend by running `yarn run start --port PORT`, replacing PORT with the port in the config file.
If using the default port, it'd look like `yarn run start --port 4340`.


## Other things
This guide does not cover using a reverse proxy, if you need assistance with that, google "reverse proxy nginx tutorial".
