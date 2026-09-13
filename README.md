# Savorly — Recipe Discovery & Meal Planner

Savorly is a full-stack Flask application for discovering recipes, saving a personal cookbook, organizing recipes into collections, adding private notes, and building simple dated meal plans.

This project was built as a Springboard Software Engineering Capstone and demonstrates full-stack development with authentication, authorization, relational databases, CRUD operations, external API integration, testing, and production deployment.

## 🌐 Live Demo

**[View Savorly Live](https://savorly-t6cx.onrender.com/)**

> Savorly is hosted on Render's free tier. The first request after a period of inactivity may take a little longer while the service wakes up.

---

## Features

- Secure user registration, login, and logout
- Recipe search powered by TheMealDB
- Forgiving recipe-name search, including joined-word differences such as `padthai`
- Browse recipes by category
- Complete recipe details with measured ingredients and instructions
- Print and Share functionality
- Save recipes to a personal cookbook
- Add private notes to saved recipes
- Filter saved recipes
- Create, edit, and delete recipe collections
- Add saved recipes to collections
- Create and manage meal plans
- Schedule recipes by date and meal type
- Per-user ownership and authorization checks
- Responsive interface for desktop and mobile
- Empty states and graceful API error handling

---

## Technology

### Backend

- Python
- Flask
- SQLAlchemy
- PostgreSQL
- Alembic / Flask-Migrate
- Gunicorn

### Frontend

- Jinja templates
- HTML
- CSS
- Vanilla JavaScript

### Testing

- pytest
- pytest-cov

### Deployment

- Render — Flask web service
- Neon — PostgreSQL production database
- GitHub — source control and deployment source

The application's Python package is still named `mealmate` for its import path, Flask application module, and local default database name. The public product name is **Savorly**.

---

## Recipe API

Savorly uses the [TheMealDB V1 API](https://www.themealdb.com/api.php) to provide recipe discovery data.

The API supplies:

- Recipe IDs
- Recipe names
- Images
- Categories
- Cuisines / areas
- Ingredients
- Measurements
- Cooking instructions

The public key `1` is used as the educational-development default. A different key can be configured through the `MEALDB_API_KEY` environment variable.

Savorly stores only an external recipe ID and minimal display metadata rather than copying the provider's entire recipe database.

---

## Database Design

| Table                | Purpose and Relationships                                             |
| -------------------- | --------------------------------------------------------------------- |
| `users`              | User accounts; each user owns their private application data          |
| `saved_recipes`      | Saved external recipes belonging to a user; also stores private notes |
| `collections`        | User-created recipe collections                                       |
| `collection_recipes` | Many-to-many relationship between collections and saved recipes       |
| `meal_plans`         | User-owned meal plans                                                 |
| `meal_plan_items`    | Connects saved recipes to meal plans with dates and meal types        |

Deleting a user cascades through owned data.

Deleting a collection does not delete the user's saved recipes.

Route-level ownership checks prevent users from accessing or modifying another user's private resources.

---

## Core User Flow

**Register → Log In → Search/Browse → View Recipe → Save → Add Note → Create Collection → Add Recipe → Create Meal Plan → Schedule Recipe**

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Pat-saya/savorly.git
cd savorly
```

### 2. Create the local PostgreSQL database

```bash
createdb mealmate
```

### 3. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy:

```bash
.env.example
```

to:

```bash
.env
```

and configure the required values.

### 6. Apply database migrations

```bash
flask --app run db upgrade
```

### 7. Start the development server

```bash
flask --app run run --debug
```

Then visit:

`http://127.0.0.1:5000`

---

## Environment Variables

| Environment Variable    | Purpose                                                          |
| ----------------------- | ---------------------------------------------------------------- |
| `SECRET_KEY`            | Signs sessions and CSRF tokens; must remain secret in production |
| `DATABASE_URL`          | PostgreSQL / SQLAlchemy database connection URL                  |
| `MEALDB_API_KEY`        | TheMealDB API key                                                |
| `MEALDB_BASE_URL`       | Optional TheMealDB base URL override                             |
| `SESSION_COOKIE_SECURE` | Set to `true` when running over HTTPS in production              |

Production credentials are configured directly through the hosting environment.

**Secrets and database credentials are never committed to GitHub.**

The `.env` file is ignored by Git.

---

## Tests

From the project root with the virtual environment activated, run:

```bash
PYTHONPATH=. pytest -W error --cov=mealmate
```

`PYTHONPATH=.` allows Python imports to resolve the local `mealmate` package.

The automated test suite covers:

- Password hashing
- Registration
- Duplicate accounts
- Login and logout
- CSRF protection
- Protected routes
- Recipe API normalization
- Empty API responses
- API error handling
- Duplicate recipe saves
- Saved recipes
- Private notes
- Collections
- Meal planning
- Validation
- Cross-user authorization

---

## Deployment

Savorly is deployed as a Python web service on **Render**.

The production PostgreSQL database is hosted separately on **Neon**.

The application is deployed from this GitHub repository, while production credentials and database connection information are supplied through secure environment variables.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

The production start command applies pending database migrations before starting Gunicorn:

```bash
flask --app run db upgrade && gunicorn run:app
```

### Production Architecture

```text
GitHub Repository
       ↓
Render Web Service
       ↓
Flask / Gunicorn
       ↓
Neon PostgreSQL Database

Flask Server
       ↓
TheMealDB API
```

### Live Application

**[https://savorly-t6cx.onrender.com/](https://savorly-t6cx.onrender.com/)**

---

## Verification Record

- Full automated tests pass with warnings treated as errors
- A CSRF-enabled end-to-end run passes against live TheMealDB search and recipe-detail data
- Initial database migrations upgrade and downgrade successfully against a fresh PostgreSQL database
- PostgreSQL catalog inspection confirms expected tables, primary keys, foreign keys, unique constraints, cascade rules, and indexes
- PostgreSQL model workflow confirms password hashing, relationships, uniqueness enforcement, and user-owned cascade deletion
- Gunicorn successfully imports and runs the production Flask application
- Production database migrations run during application startup
- Application successfully deploys to Render
- Production PostgreSQL database is hosted on Neon

---

## Security

Savorly includes several security measures:

- Password hashing
- Session-based authentication
- CSRF protection
- Per-user authorization
- Ownership validation for private resources
- Secure production session cookies
- Environment-based secret configuration
- Database credentials excluded from source control

Users cannot access or modify another user's saved recipes, notes, collections, or meal plans through protected application routes.

---

## Project Structure

```text
savorly/
├── mealmate/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── forms.py
│   ├── routes/
│   └── services/
├── migrations/
├── tests/
├── run.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
└── README.md
```

The exact internal organization may evolve as the project is maintained, but the application separates database models, routes, templates, static assets, API/service logic, migrations, and tests.

---

## What I Learned

Building Savorly gave me practical experience connecting multiple parts of a full-stack application rather than treating each feature independently.

The project required me to work with:

- Relational database design
- SQLAlchemy relationships
- Authentication and authorization
- CRUD workflows
- External API integration
- Server-side rendering
- Form validation and CSRF protection
- Automated testing
- Environment variables
- Database migrations
- Production deployment
- PostgreSQL hosting

One important design decision was separating external recipe data from user-owned application data. TheMealDB provides recipe discovery content, while Savorly's PostgreSQL database stores the user's relationships with those recipes, including saves, notes, collections, and meal plans.

---

## Submission Checklist

- [x] GitHub repository available
- [x] Live deployment available
- [x] Production environment variables configured
- [x] Production PostgreSQL database configured
- [x] Initial database migration verified
- [x] Automated tests run with warnings enabled
- [x] Local end-to-end flow verified against the live recipe API
- [ ] Verify the complete deployed end-to-end user flow
- [ ] Add 2–4 application screenshots to this README
- [x] Confirm no secrets or temporary files are tracked
- [ ] Complete final keyboard-navigation and mobile-layout review

---

## Interview Explanation

> Savorly is a full-stack Flask and PostgreSQL application that turns an external recipe catalog into user-owned workflows. TheMealDB supplies recipe discovery content, while my relational database stores accounts, saved recipe metadata, private notes, many-to-many collections, and dated meal-plan entries. I focused on secure authentication, ownership authorization, relational database design, testable service boundaries, and production deployment. The Flask application is deployed on Render and uses a Neon-hosted PostgreSQL database in production.
