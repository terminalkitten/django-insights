---
title: Development
description: Run the demo project, the tests, the dashboard stylesheet build and these docs.
sidebar:
  order: 8
---

For contributors. The repository has a demo project (a fictional chat and billing app) with a lot of seeded data, so every chart type has something to show.

## Set up

:::steps
1. Install the dependencies with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

2. Create the databases, fill them and collect the insights:

   ```bash
   make migrate
   make seed
   make collect_insights
   ```

3. Start the server and open <http://localhost:8000/>. The demo serves the dashboard at the root and logs you in automatically.

   ```bash
   make rs
   ```
:::

`make clean` deletes the databases and migrates again.

## Tests and checks

```bash
make lint
```

This runs ruff, `ty` and pytest, and pytest fails under 90% coverage. `uv run tox run` runs the whole matrix (Python 3.11 to 3.14, Django 5.2 to 6.1, and the lowest supported versions).

## The dashboard stylesheet

The dashboard uses [Basecoat](https://basecoatui.com) compiled with Tailwind 4, one stylesheet per style. After you change a template class or the sources, rebuild them:

```bash
cd django_insights/packages
pnpm install
pnpm build
```

## The theme colors

`django_insights/palettes.py` is generated from the shadcn/ui themes, do not edit it by hand. See [Theming](theming.md#updating-the-colors).

## These docs

The docs are built with [dokk](https://github.com/terminalkitten/dokk) from the `docs` folder.

```bash
uv run dokk serve
uv run dokk check
```

Pushing to `main` builds and publishes them to GitHub Pages.
