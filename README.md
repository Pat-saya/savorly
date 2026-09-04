# Savorly — Recipe Discovery & Meal Planner

Savorly is a full-stack Flask application for finding recipes, saving a personal cookbook, organizing recipes into collections, adding private notes, and building simple dated meal plans. It is a Springboard capstone focused on database relationships, authentication, authorization, CRUD, and external API integration.

## Features

- Secure registration, login, and logout
- Forgiving recipe-name search, including common joined-word spacing differences (for example `padthai`)
- Browse recipes by TheMealDB category (preferred Browse cards plus a Discover category filter)
- Complete recipe details with measured ingredients and instructions
- Print and Share (native share when available, plus email and copy-link fallbacks)
- Saved recipes, private notes, and saved-recipe filtering
- Collection create/read/update/delete and recipe membership
- Meal-plan create/read/update/delete with dates and meal types
- Ownership checks on every private resource
- Responsive interface, empty states, and graceful API errors

## Technology

Python, Flask, PostgreSQL, SQLAlchemy, Alembic/Flask-Migrate, Jinja, HTML, CSS, small vanilla JavaScript enhancements, pytest, and Gunicorn.

The application Python package is still named `mealmate` (import path, Flask app module, and local default database name). The product UI and deployment service name are **Savorly**.

## Recipe API

Savorly uses the [TheMealDB V1 API](https://www.themealdb.com/api.php) from the server. It provides IDs, names, images, categories, cuisines/areas (as recipe metadata), measurements, ingredients, and instructions. The public key `1` is the local educational-development default; use `MEALDB_API_KEY` for a supporter key before a public production release, following the provider's current guidance. Savorly saves only an external ID and minimal display metadata—not a copy of the provider database.

## Database design

| Table | Purpose and relationships |
| --- | --- |
| `users` | `id` primary key; owns every private object |
| `saved_recipes` | `id` primary key; `user_id` foreign key; unique external recipe per user; includes private note |
| `collections` | `id` primary key; `user_id` foreign key; unique name per user |
| `collection_recipes` | Composite primary key and two foreign keys implementing collection ↔ saved-recipe many-to-many |
| `meal_plans` | `id` primary key; `user_id` foreign key |
| `meal_plan_items` | `id` primary key; foreign keys to plan and saved recipe; adds date and meal type |

Deleting a user cascades through owned data. Deleting a collection keeps saved recipes. Route-level owner checks prevent cross-account access.

## Local setup

1. Install Python 3.11+ and PostgreSQL.
2. Run `createdb mealmate` (local default database name used by `.env.example` and the app default).
3. Run `python3 -m venv .venv`, then `source .venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env` and replace `SECRET_KEY`.
6. Run `flask --app run db upgrade`.
7. Run `flask --app run run --debug` and visit `http://127.0.0.1:5000`.

| Environment variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs sessions and CSRF tokens; must be secret in production |
| `DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `MEALDB_API_KEY` | TheMealDB key; defaults to development key `1` |
| `MEALDB_BASE_URL` | Optional provider base URL override |
| `SESSION_COOKIE_SECURE` | Set to `true` for HTTPS production deployment |

Never commit `.env`; it is ignored by Git.

## Tests

From the project root with the virtualenv activated:

```bash
PYTHONPATH=. pytest -W error --cov=mealmate
```

`PYTHONPATH=.` is required so imports resolve the local `mealmate` package. The suite uses in-memory SQLite and mocked API responses. It covers password hashing, duplicate accounts, login/logout, CSRF rejection, protected pages, API normalization plus empty/error states, duplicate saves, the saved → note → collection → meal-plan workflow, validation, and cross-user authorization.

## Deployment

`render.yaml` defines a Render web service and managed PostgreSQL database, generated secret, secure session cookie, `/health` check, migration command, and Gunicorn process. The start command is:

```bash
flask --app run db upgrade && gunicorn run:app
```

Before public launch, set a production-appropriate TheMealDB key and confirm current provider terms. Then verify registration, login, search, browse by category, save, collections, notes, meal planning, print/share, logout, and mobile layout on the deployed URL.

## Verification record

- Full tests pass with warnings treated as errors.
- A CSRF-enabled end-to-end run passes against live TheMealDB search/detail data.
- The initial migration upgrades and downgrades cleanly against a fresh PostgreSQL 16 database.
- PostgreSQL catalog inspection confirms all expected tables, primary keys, foreign keys, unique constraints, cascade rules, and indexes.
- A PostgreSQL model workflow confirms hashing, relationships, uniqueness enforcement, and user-owned cascade deletion.
- Gunicorn imports the production application successfully.
- The Render Blueprint parses successfully and follows the current Blueprint field structure.

## Core user flow

Register → search by name or browse by category → open recipe → save → write note → create collection → add recipe → create meal plan → schedule recipe.

## Submission checklist

- [ ] Add GitHub repository and live deployment URLs
- [ ] Configure production environment variables and API key
- [x] Verify the initial migration from a clean PostgreSQL database
- [x] Run all automated tests with warnings enabled
- [x] Verify the local end-to-end flow against the live recipe API
- [ ] Verify the deployed end-to-end flow
- [ ] Add 2–4 screenshots to this README
- [x] Confirm no secrets or temporary files are tracked
- [ ] Check keyboard navigation, form labels, and mobile layout

## Interview explanation

“Savorly is a Flask and PostgreSQL app that turns an external recipe catalog into user-owned workflows. The API supplies discovery content, while my relational database stores accounts, saved recipe metadata, private notes, many-to-many collections, and dated meal-plan entries. I emphasized secure authentication, ownership authorization, testable service boundaries, and a deployable scope.”
