# Echo

Run development environment:

```sh
cp example.config.json config.json
vim config.json  # Edit the config

# Run developemnt environment, then remove it again to prevent auto restarts
PROFILE=dev sh -c 'docker compose up --build --watch && docker compose down'
```

To run a production-like setup instead run `docker compose up`.
