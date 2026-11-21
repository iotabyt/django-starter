# django-starter

Iotabyt's full-stack Django starter, as a [Copier](https://copier.readthedocs.io) template.
Server-rendered first, few moving parts: Django 6, htmx and template partials, Tailwind v4,
allauth (email, Google, MFA), Procrastinate jobs in Postgres, the Unfold admin, and boring
Kamal 2 deploys to your own server. Organizations and a React SPA are optional.

## What you get

A freshly generated project with the defaults (`use_spa` and `use_orgs` on), straight after
`bin/setup` and `bin/dev`, with a little demo data. Screenshots live in [`screenshots/`](screenshots/).

| | |
|---|---|
| **Landing page**<br>![Landing page](screenshots/home.png) | **Signed in: home and profile menu**<br>![Signed-in home with the profile menu open](screenshots/home-signed-in.png) |
| **Sign in** (email, or Google when configured)<br>![Sign in](screenshots/sign-in.png) | **Sign up**<br>![Sign up](screenshots/sign-up.png) |
| **Dashboard** (React SPA at `/app/`)<br>![Dashboard](screenshots/dashboard.png) | **Organization: members, roles and invites**<br>![Organization page](screenshots/organization.png) |
| **Settings: profile**<br>![Profile settings](screenshots/settings-profile.png) | **Settings: email addresses**<br>![Email settings](screenshots/settings-email.png) |
| **Settings: two-factor authentication**<br>![Two-factor settings](screenshots/settings-two-factor.png) | **Accepting an invite**<br>![Invite page](screenshots/invite.png) |
| **Organization page without the SPA** (`use_spa=false`, server-rendered with htmx)<br>![Server-rendered organization page](screenshots/organization-server-rendered.png) | **Admin** (Unfold)<br>![Unfold admin](screenshots/admin.png) |

Dark mode follows the operating system, and a toggle in the navbar (on the server pages and
in the SPA) lets people choose:

| | |
|---|---|
| **Sign in**<br>![Sign in in dark mode](screenshots/sign-in-dark.png) | **Signed in: home and profile menu**<br>![Signed-in home in dark mode](screenshots/home-signed-in-dark.png) |
| **Dashboard**<br>![Dashboard in dark mode](screenshots/dashboard-dark.png) | **Organization**<br>![Organization page in dark mode](screenshots/organization-dark.png) |

On a phone:

<p>
  <img src="screenshots/mobile-home.png" alt="Landing page on a phone" width="260">
  &nbsp;
  <img src="screenshots/mobile-dashboard.png" alt="Dashboard on a phone" width="260">
  &nbsp;
  <img src="screenshots/mobile-dashboard-dark.png" alt="Dashboard on a phone in dark mode" width="260">
</p>

## Use it

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # 0. uv, if you don't have it yet
uvx copier copy gh:iotabyt/django-starter my-app   # 1. generate
cd my-app
bin/setup                                          # 2. git init, .env, Postgres, packages, database, CSS
bin/dev                                            # 3. http://localhost:8000
```

uv is the only hard requirement, plus Docker **or** an existing Postgres (`bin/setup` uses
whatever `DATABASE_URL` points at if it's reachable, and only starts Docker Compose
otherwise) and Node 22+ for the SPA. [just](https://just.systems) is optional
(`uv tool install rust-just`) and adds shortcuts such as `just test`. The generated
project's README covers development and deployment.

### Options

| Question | Default | Notes |
|---|---|---|
| `project_name` | `My Project` | Human-readable name |
| `project_slug` | derived from the name | `^[a-z][a-z0-9-]*$`; service, image and package name. The database name is the slug with `_` for `-` |
| `description` | empty | |
| `author_name` | `Frank Owusu Boakye` | |
| `author_email` | `hello@iotabyt.com` | |
| `domain` | `<slug>.iotabyt.com` | Public hostname served by kamal-proxy |
| `github_owner` | `iotabyt` | Images go to `ghcr.io/<owner>/<slug>` |
| `registry_username` | `oboynitro` | GitHub user that owns the GHCR token (not the org); `registry.username` in `deploy.yml` |
| `server_host` | `vps-01` | Tailscale name of the server |
| `database` | `accessory` | `accessory`: Postgres 18 on the server as a Kamal accessory. `external`: bring your own `DATABASE_URL` (Neon etc.) |
| `use_orgs` | `true` | `apps/orgs`: organizations, memberships with roles, email invites |
| `use_spa` | `true` | `apps/api` (Django Ninja) and `frontend/` (React 19, Vite, TanStack Router and Query) at `/app/` |

Answer non-interactively with `--defaults -d use_spa=false -d database=external`.

### Pull in template updates

Your answers are saved in `.copier-answers.yml`, so later improvements can be merged into an
existing project:

```bash
copier update          # from a clean git working tree; resolve any conflicts, then commit
```

## Working on the template

Everything generated lives in `template/` (`_subdirectory`).

- **Only files ending in `.jinja` are rendered** (and lose the suffix). Everything else is
  copied as-is, which is how Django templates keep their own `{{ }}` and `{% %}`. Never give
  a Django template a `.jinja` suffix.
- **Optional parts use conditional names**, which Copier skips when they render empty:
  `apps/{% if use_orgs %}orgs{% endif %}/`, `{% if use_spa %}frontend{% endif %}/`,
  `templates/{% if use_spa %}spa.html{% endif %}`.
- **Whitespace:** `copier.yml` turns on `trim_blocks` and `lstrip_blocks`, so put
  `{% if %}` / `{% endif %}` on their own lines (indented or not) and they leave nothing
  behind. Don't end a content line with a block tag (its newline would be eaten); use an
  inline expression such as `{{ ', Vite' if use_spa else '' }}` instead. just's own
  variables are escaped as `{{ '{{args}}' }}`. Always check the generated output: Ruff's
  isort and format checks catch most mistakes.
- `db_name` is a computed value (`when: false`): usable in templates, never asked or stored.

### Test every combination

Commit first (`--vcs-ref HEAD` renders the committed tree), then generate all four
`use_spa` × `use_orgs` combinations, alternating `database`:

```bash
uvx copier copy --defaults --vcs-ref HEAD -d use_spa=true -d use_orgs=false -d database=external . /tmp/t-spa
cd /tmp/t-spa
bin/setup && bin/setup      # the second run proves it's idempotent
uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run basedpyright
uv run python manage.py makemigrations --check --dry-run
npm --prefix frontend ci && npm --prefix frontend run build && npm --prefix frontend run typecheck
```

Also grep the output for leftover `{{` / `{%` outside `templates/` and the justfile.
`.github/workflows/template.yml` does all of this in CI for every combination.

### Regenerating migrations

Migrations are generated, then copied back into the template. Generate `users` first and
`orgs` in a separate run (generating both together can split orgs into two files):

```bash
uvx copier copy --defaults --vcs-ref HEAD -d use_spa=false . /tmp/t-mig && cd /tmp/t-mig
rm apps/users/migrations/0001_initial.py "apps/orgs/migrations/0001_initial.py"
uv sync                     # makemigrations doesn't need a database
uv run python manage.py makemigrations users
uv run python manage.py makemigrations orgs
```

Copy `apps/users/migrations/*.py` to `template/apps/users/migrations/` and
`apps/orgs/migrations/*.py` to `template/apps/{% if use_orgs %}orgs{% endif %}/migrations/`.

### Frontend lockfile and route tree

`frontend/package-lock.json.jinja` is a real lockfile with `{{ project_slug }}-frontend` in its
two `name` fields. After changing `package.json.jinja`, run `npm install` in a generated
project and copy the lockfile back, restoring those two names. Copy back
`src/routeTree.gen.ts` too if you add routes (it's committed so `tsc` works on a fresh clone).

## Licence

MIT. See [LICENSE](LICENSE).
