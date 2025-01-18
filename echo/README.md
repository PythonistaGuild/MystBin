# Echo

Run development environment:

```sh
cp example.config.json config.json
vim config.json # Edit to your liking

PROFILE=dev sh -c 'docker compose up --build --watch'
```

To run a production-like setup instead run `docker compose up`.
