# PantryChef 🥦

A smart pantry management and recipe recommendation web app that helps you stop wasting food and answer the daily question of *"what should I cook tonight?"*

---

## What it does

- **Scan your groceries** — point your camera at your haul, and PantryChef identifies every item using AI. No typing required.
- **Track expiry dates** — items without a date get an AI-estimated shelf life automatically. Your pantry is colour-coded by urgency.
- **Get alerted before things expire** — daily email with items nearing expiry and a direct link to recipes that use them.
- **Recipes built around your pantry** — GPT-4o generates personalised recipe suggestions from what you actually have, respecting your dietary preferences, allergies, spice tolerance, cuisine preference, and nutrition goals.
- **Full nutrition and allergen info** — every suggested recipe shows a per-serving breakdown and flags any allergens that match your profile.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite) + TailwindCSS |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| AI / Vision | OpenAI GPT-4o |
| Email Alerts | AWS SES |
| Deployment | AWS (EC2, RDS, S3, CloudFront) |

---

## Project Structure

```
pantrychef/
├── backend/          # FastAPI application
├── frontend/         # React application
├── docs/             # Requirements and architecture documents
├── README.md
└── .gitignore
```

---

## Documentation

- [Software Requirements Document](docs/requirements.md)

---

## Local Setup

> Coming soon — setup instructions will be added once the project scaffold is complete.

---

## Status

🚧 In development
