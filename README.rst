.. image:: res/mystbin_logo_light_full.svg?raw=True
    :align: center

.. class:: center
Easily share your code or text with syntax highlighting and themes for readability.

**NOTE: This software in under heavy development and subject to change. At this time it is also not supported.**


.. image:: https://img.shields.io/badge/Python-3.8%20%7C%203.9-blue.svg
    :target: https://www.python.org
    
.. image:: https://img.shields.io/github/license/EvieePy/Wavelink.svg
    :target: LICENSE
    
.. image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
    :target: https://discord.gg/RAKc3HF
    
.. image:: https://github.com/PythonistaGuild/MystBin/workflows/Analyze/badge.svg
    :target: https://github.com/PythonistaGuild/actions?query=workflow%3AAnalyze
    
.. image:: https://github.com/PythonistaGuild/MystBin/workflows/Lint%20Code%20Base/badge.svg
    :target: https://github.com/PythonistaGuild/MystBin/actions?query=workflow%3A%22Lint+Code+Base%22
   
   
--------------
Installation
--------------

Pre-requisites
================

We have provided a `docker-compose.yml` file for use in Docker with Docker Compose.

Setting up
============

1. Make a copy of `config-template.toml` named `config.toml` and change the contents to match your environment.
2. Make a copy of `.env-template` as `.env` and edit to match your environment.

The template files have similar values to what is expected.

.. code-block:: sh

    docker-compose up -d --build

Which will build the project and use your desired configuration.
