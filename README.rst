.. raw:: html

    <h1 align="center">
        <sub>
            <img src="res/logo_mini.svg" height="36">
        </sub>
        MystBin!
    </h1>
    <p align="center">Easily share your code or text with syntax highlighting and themes for readability.</p>
    <p align="center"><b>NOTE: This software in under heavy development and subject to change. At this time it is also not supported.</b?></p>

.. raw:: html

    <p align="center">
        <img alt="Python" src="https://img.shields.io/badge/Python-3.8%20%7C%203.9-blue.svg" />

        <img alt="License" src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" />

        <a href="https://discord.gg/RAKc3HF">
            <img alt="License"
                src="https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white" />
        </a>

        <a href="https://github.com/PythonistaGuild/actions?query=workflow%3AAnalyze">
            <img alt="Analysis Status"
                src="https://github.com/PythonistaGuild/MystBin/workflows/Analyze/badge.svg" />
        </a>

        <a href="https://github.com/PythonistaGuild/MystBin/actions?query=workflow%3A%22Lint+Code+Base%22">
            <img alt="Linting Status"
                src="https://github.com/PythonistaGuild/MystBin/workflows/Lint%20Code%20Base/badge.svg" />
        </a>
    </p>

----------

Installation
------------

.. raw:: html

    <h2 align="left"><b>Pre-requisites</b></h2>

We have provided a ``docker-compose.yml`` file for use in Docker with Docker Compose.


.. raw:: html

    <h2 align="left">Setting up</h2>

1. Make a copy of ``config-template.toml`` named ``config.toml`` and change the contents to match your environment.
2. Make a copy of ``.env-template`` as ``.env`` and edit to match your environment.

The template files have similar values to what is expected.

.. code-block:: sh

    docker-compose up -d --build

Which will build the project and use your desired configuration.