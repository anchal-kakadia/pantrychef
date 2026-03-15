**PantryChef**

Smart Pantry Management & Recipe Recommendation System

**Software Requirements Document**

Version 1.0 — March 2025

# 1. Introduction

## 1.1 Purpose of This Document

This Software Requirements Document (SRD) defines the functional and non-functional requirements for PantryChef. It captures what the system should do, who it is for, and what constraints it must operate within. This document will serve as the reference point throughout design, development, and testing.

## 1.2 Scope

PantryChef is a web application that helps users manage the food items in their home and decide what to cook. It tracks pantry contents, alerts users before items expire, and recommends personalized recipes based on what is available and what the user prefers to eat.

The first version of the system is a web application. A mobile application is identified as a future phase and is out of scope for this document.

## 1.3 Definitions and Abbreviations

| **Term** | **Meaning** |
| --- | --- |
| SRD | Software Requirements Document |
| LLM | Large Language Model — an AI model that generates text from a prompt |
| GPT-4o | OpenAI's multimodal model capable of processing both text and images |
| Vision AI | Use of an AI model to interpret and extract information from an image |
| Shelf life | The estimated number of days a food item remains safe to use after purchase |
| Allergen | An ingredient that may cause an allergic reaction (e.g. nuts, dairy, gluten) |
| Pantry | In this system, a user's complete collection of tracked food items at home |
| AWS SES | Amazon Simple Email Service — a cloud-based email sending service |
| JWT | JSON Web Token — a method for securely representing user authentication state |
| FastAPI | A modern Python web framework for building APIs |
| APScheduler | A Python library for scheduling background jobs at set times or intervals |

## 1.4 Document Overview

Section 2 describes the problem being solved. Section 3 identifies the users. Section 4 lists high-level goals. Section 5 details all functional requirements. Section 6 covers non-functional requirements. Section 7 defines the system architecture and tech stack. Section 8 describes the database design. Section 9 lists the API surface. Section 10 defines the scope boundary between this version and future phases.

# 2. Problem Statement

## 2.1 Food Waste at Home

A common pattern in households is: groceries are purchased, placed in the fridge or cupboard, and then forgotten. Items expire before they are used because there is no clear visibility into what is in the pantry or how long it will last. This results in regular food waste that could be avoided with timely reminders.

## 2.2 Meal Decision Friction

Even when food is available at home, deciding what to cook is a recurring difficulty. People default to familiar meals, over-rely on food delivery, or spend time searching recipe websites that assume ingredients they do not have. There is no tool that bridges the specific gap between the contents of a person's actual pantry and a recipe suggestion tailored to their preferences.

## 2.3 Lack of Personalized Dietary Awareness

Generic recipe platforms do not account for the specific combination of a user's dietary restrictions, allergies, nutritional goals, spice tolerance, and cultural food preferences simultaneously. Users with any of these constraints must manually filter or verify recipes, which is time-consuming and error-prone — especially for allergy safety.

## 2.4 Manual Data Entry Friction

Pantry tracking apps that require users to type in each item individually see low adoption because the effort outweighs the perceived benefit. A user returning home with ten items of produce should not need to enter each one manually. A faster input method is required for the app to be used consistently.

# 3. Users

## 3.1 Target Users

PantryChef is intended for individuals who cook at home and manage their own groceries. This includes people living alone, students, working adults, and small households. There is a single user role in this version of the system.

## 3.2 User Personas

|  | **Neha** | **Rajan** | **Priya** |
| --- | --- | --- | --- |
| Description | Working professional, cooks on weeknights | Student, tracks nutrition carefully | Home cook, manages a household with dietary restrictions |
| Core problem | Forgets what is in the fridge; wastes food weekly | Wants high-protein meals from what he already has | Needs to avoid allergens for family members |
| Preference needs | Quick meals, mild spice | High protein, balanced carbs | Indian cuisine, no nuts, moderate spice |
| Alert need | Email before items expire | Daily recipe suggestion email | Weekly summary with meal ideas |

## 3.3 User Assumptions

* Users have a basic level of comfort using a web browser.
* Users have an email address they check regularly.
* Users have access to a device with a camera or the ability to upload photos (for the photo-scan feature).
* Users are not assumed to have any technical knowledge.

# 4. Goals

## 4.1 Primary Goals

* Allow users to track food items in their pantry with minimal effort.
* Alert users before items expire so they can use them in time.
* Recommend recipes based on what is currently in the pantry.
* Respect dietary preferences, allergies, nutritional goals, spice tolerance, and cultural preferences in every recommendation.
* Provide clear allergen and nutrition information on every suggested recipe.

## 4.2 Secondary Goals

* Reduce the time it takes to add grocery items to the pantry through AI-assisted photo scanning.
* Allow users to save and revisit past recipes they liked.
* Allow users to build a shopping list from missing ingredients.

## 4.3 Out of Scope (Version 1)

* Mobile application (iOS or Android).
* SMS or push notifications.
* Barcode scanning for product entry.
* Integration with grocery stores or delivery services.
* Multi-user households or shared pantries.
* Social or community features (sharing recipes, following other users).

# 5. Functional Requirements

## 5.1 User Account Management

**5.1.1 Registration**

* A new user can create an account by providing their name, email address, and a password.
* The email address must be unique across all accounts.
* Passwords must be at least 8 characters.
* On successful registration, the user is redirected to the profile setup wizard.

**5.1.2 Login and Session**

* A registered user can log in with their email and password.
* On successful login, the system issues a JWT that the frontend stores and includes in subsequent API requests.
* Sessions expire after 24 hours, after which the user must log in again.

**5.1.3 User Profile**

During onboarding and at any point thereafter, the user can set or update the following preferences. These preferences are stored in the database and used in every recipe recommendation request.

| **Preference** | **Accepted Values / Notes** |
| --- | --- |
| Dietary preference | Vegetarian, vegan, pescatarian, omnivore, other |
| Nutritional goal | High protein, low carb, low calorie, balanced, no specific goal |
| Allergies | Free-form list — e.g. nuts, dairy, gluten, shellfish, eggs, soy; user can add custom entries |
| Spice tolerance | Mild, medium, hot, very hot |
| Cuisine preference | Indian, Mediterranean, East Asian, Western, Middle Eastern, other; user may select multiple |

## 5.2 Pantry Management

**5.2.1 Photo-Based Item Entry**

This is the primary method for adding items to the pantry. It is designed to eliminate the need to type each item individually after a grocery run.

**Intended use — one photo, many items**

A single photo is expected to capture multiple grocery items at once. The intended flow is for the user to lay all their purchases out on a counter or table and photograph the whole haul in one shot. GPT-4o Vision will identify all visible items from that single image. This means 3 scans per day is a generous limit — most users will need only 1.

* Each user is allowed a maximum of 3 new scan sessions per day. This limit resets at midnight.
* All LLM-based endpoints require the user to be logged in. Anonymous scanning is not permitted.
* Before the user opens the camera or file picker, the system displays a short guidance prompt:
* "Lay all your groceries out on a flat surface and take one photo of everything together for the best results. Items inside bags cannot be detected."

**Scan flow**

* The user clicks "Scan Groceries" and uploads or captures a photo.
* The system sends the image to GPT-4o Vision. The expected response is a JSON array where each element contains: name, category, estimated quantity, and unit.
* The system displays a confirmation screen listing all detected items as editable cards.
* For each card the user can: edit the name and category, adjust the quantity and unit (required — quantity is difficult to infer reliably from a photo alone), and optionally enter an expiry date.
* The user can remove any incorrectly detected item before saving.
* Pressing "Add to Pantry" saves all confirmed items in a single batch operation.
* For any item where no expiry date was entered, shelf-life inference (see 5.2.3) runs automatically as part of the same save operation.

**Rescan for missed items**

If the photo missed some items, the user should not need to burn a second daily scan. The following rescan flow applies within the same session.

* On the confirmation screen, the user sees a "Some items missing?" prompt with a "Rescan" button.
* Clicking Rescan opens the camera or file picker again without counting against the daily limit.
* Each original scan session allows a maximum of 2 free rescans.
* After the second failed rescan, if items are still missing, the system displays the message: "We weren't able to pick up the remaining items. Please add them manually below." A manual entry form is shown inline so the user can type the missed items without leaving the screen.
* This ensures the user always has a path forward regardless of photo quality.

**When the daily scan limit is reached**

* Once a user has used all 3 scan sessions for the day, the "Scan Groceries" button is replaced with a message: "You've used all 3 scans for today. Scans reset at midnight. You can still add items manually."
* The manual entry option always remains fully available regardless of scan usage.

**5.2.2 Manual Item Entry**

Available as a fallback for items not visible in a photo, such as spices or items already stored out of sight.

* The user opens a form and enters item name (required), category (required), quantity (required), unit (required), and expiry date (optional).
* On save, if no expiry date was provided, shelf-life inference runs automatically.

**5.2.3 Shelf-Life Inference**

When a pantry item is added without an expiry date, the system estimates one using the LLM.

* The system sends the item name and category to GPT-4o with a prompt asking for an estimated shelf life in days for typical household storage conditions.
* The returned number of days is added to the current date to produce an estimated expiry date.
* Items with AI-estimated expiry dates are stored with a flag indicating the date is an estimate and are shown in the UI with a visible indicator (e.g. a small icon or label).
* Results for common item names are cached in a database table to avoid redundant API calls for items like "spinach" or "milk" that many users will add.

**5.2.4 Pantry Dashboard**

* The dashboard shows all active pantry items belonging to the logged-in user.
* Items are grouped by category (e.g. Vegetables, Dairy, Grains, Proteins, Condiments).
* Each item displays: name, quantity and unit, expiry date, and whether the date is AI-estimated.
* Items are colour-coded by time remaining:
* Green — more than 7 days until expiry.
* Amber — 3 to 7 days until expiry.
* Red — fewer than 3 days until expiry or already expired.
* The user can edit any item's details.
* The user can delete an item or mark it as used. Both actions remove it from the active pantry view. Marked-as-used items are retained in the database for future analytics.

## 5.3 Expiry Alerts

**5.3.1 Alert Mechanism**

* A background job runs once daily at a time configured by the user (default: 8:00 AM).
* The job checks each user's pantry for items whose expiry date falls within that user's alert threshold (default: 3 days).
* If any such items are found, the system sends the user an email listing those items.
* The email includes a direct link that opens the recipe recommendation screen with the expiring items pre-selected.
* The email also presents two action buttons for each flagged item: "Mark as Used" and "Discard". These allow the user to update their pantry directly from the email without needing to open the app.
* Items are not automatically removed from the pantry when they reach or pass their expiry date. This is intentional — users may forget to update the app, and many people continue using ingredients for a day or two after the listed expiry date. Items remain in the pantry until the user explicitly takes one of the following actions: marks the item as used, clicks Discard from the alert email, or manually deletes the item from the pantry dashboard.
* If no items are found within the threshold, no email is sent that day.

**5.3.2 Alert Configuration**

* The user can turn alerts on or off.
* The user can set the threshold: how many days in advance they want to be notified (between 1 and 7 days).
* The user can set the preferred delivery time for the daily alert email.

**5.3.3 Email Delivery**

* Emails are sent via AWS Simple Email Service.
* The email format is HTML, clearly listing item name, quantity, and days until expiry for each flagged item.
* Each item in the email has two action buttons — "Mark as Used" and "Discard" — which call the respective API endpoints via tokenized links so the user can act without logging in to the app.

## 5.4 Recipe Recommendations

**5.4.1 Pantry-Based Mode**

The user can request recipe suggestions based on what they currently have in their pantry.

* The user navigates to the Recipes screen and selects "Cook from Pantry".
* The user can optionally toggle "Prioritize expiring items", which adds a bias in the prompt toward using ingredients with the closest expiry dates.
* The user may also apply temporary session-level filters before generating suggestions. These are one-time overrides for the current request only and do not modify the user's stored profile preferences. Available session filters are:
* Cuisine override — e.g. "Any cuisine", "Indian", "Italian". Overrides the stored cuisine preference for this request.
* Health mode — Healthy, Balanced, or Cheat Meal. Adjusts the nutritional bias of the prompt.
* Meal type — Quick Meal (under 30 minutes), Comfort Food, Light Meal, or No preference.
* The system constructs a prompt for GPT-4o that includes: the user's current pantry contents, dietary preference, allergy list, nutritional goal, spice tolerance, cuisine preference, and any session-level filter overrides selected for this request. If the expiring items toggle is enabled, the prompt also instructs GPT-4o to prioritize those ingredients.
* GPT-4o returns between 3 and 5 recipe suggestions in the structured JSON format described in 5.4.3.
* The frontend renders these as recipe cards the user can browse and expand.
* Each recipe request counts against the user's daily limit of 10 recipe generation requests (see Section 6.6).

**5.4.2 General Browse Mode**

The user can also ask for recipe ideas without being constrained to their pantry.

* The user selects "Browse Recipes" and can optionally specify a mood, occasion, or cuisine type.
* The same user preferences (dietary, allergy, spice, cuisine, nutrition goal) are included in the prompt. Session-level filters from 5.4.1 are also available here.
* GPT-4o returns recipe suggestions along with the full ingredient list including items the user may not have.
* Any missing ingredients can be added to the user's shopping list directly from the recipe view.
* Each request in this mode also counts against the daily limit of 10 recipe generation requests (see Section 6.6).

**5.4.3 Recipe Data Structure**

Every recipe returned by the system, regardless of mode, must contain the following fields. The LLM is prompted to return this as structured JSON to ensure consistent rendering.

| **Field** | **Description** |
| --- | --- |
| title | Name of the recipe |
| description | A 2 to 3 sentence summary of the dish |
| cook\_time\_minutes | Estimated total time including preparation |
| servings | Number of servings the recipe produces |
| ingredients | Array of objects: { name, quantity, unit } |
| steps | Ordered array of instruction strings |
| nutrition\_per\_serving | Object: { calories, protein\_g, carbs\_g, fat\_g, fibre\_g } — approximate values |
| allergens\_present | Array of allergen strings identified in the recipe ingredients |
| allergen\_warning | Boolean — true if any item in allergens\_present matches the user's declared allergies |
| tags | Array of descriptive tags, e.g. ["high-protein", "spicy", "under 30 minutes"] |

**5.4.4 Allergen Safety Check**

Allergen detection must not rely solely on the LLM output, because generative models can occasionally miss an ingredient.

* After receiving the GPT-4o response, the backend cross-references the allergens\_present field against the user's stored allergy list.
* If any match is found, the allergen\_warning field is set to true in the response returned to the frontend, regardless of what GPT returned.
* The frontend must display a clearly visible warning banner on any recipe card where allergen\_warning is true.
* The recipe is not hidden or removed — the user may still wish to view it and substitute an ingredient — but the warning must be impossible to miss.

**5.4.5 Nutrition Display**

* Every recipe card shows a nutrition summary section: calories, protein, carbohydrates, fat, and fibre per serving.
* Values are labelled as approximate since they are LLM-generated estimates, not computed from a verified nutritional database.

**5.4.6 Save and Rate Recipes**

* The user can save any recipe to their personal recipe book.
* Saved recipes persist in the database and can be viewed from a dedicated Saved Recipes screen.
* The user can rate a saved recipe as liked or disliked.
* Ratings from past recipes are included as context in future recipe recommendation prompts to influence suggestions toward what the user has preferred.

## 5.5 Shopping List

* The user can add items to a shopping list manually.
* When viewing a recipe in General Browse mode, any ingredients the user does not currently have in their pantry can be added to the shopping list in one click.
* Each shopping list item shows: name, quantity, and unit.
* When the user marks an item as purchased, the system immediately prompts them to confirm the quantity and optionally enter an expiry date, then adds it to the pantry.
* The user can delete items from the shopping list.

## 5.6 Analytics Dashboard

This feature is lower priority and can be deferred but is included here to define the intended behaviour for when it is implemented.

* A summary screen shows the user a weekly breakdown of items used versus items wasted (expired and removed without being used).
* A section shows the distribution of recipe categories cooked (e.g. 40% Indian, 30% Mediterranean).
* A streak counter shows how many consecutive days the user cooked at least one meal using pantry items.

# 6. Non-Functional Requirements

## 6.1 Performance

* All API responses not involving an LLM call must complete within 2 seconds under normal load.
* LLM-dependent responses (recipe generation, photo scanning, shelf-life inference) must complete within 15 seconds. If the response takes longer, the frontend must show a loading indicator rather than appearing unresponsive.

## 6.2 Security

* Passwords must be hashed using bcrypt before storage. Plaintext passwords must never be stored or logged.
* All API routes that access user data must require a valid JWT. Unauthenticated requests must receive a 401 response.
* All secrets (API keys, database credentials, JWT signing keys) must be stored as environment variables and never committed to the code repository.
* HTTPS must be enforced for all communication between the frontend and backend.

## 6.3 Reliability

* The daily alert job must log any failures and retry at least once before giving up for that day's run.
* If the LLM API is unavailable or returns an error, the system must return a clear error message to the user rather than crashing. The pantry item should still be saved without an estimated expiry date in this case.

## 6.4 Usability

* A new user must be able to complete registration, set up their profile, add their first pantry item, and receive a recipe suggestion without needing any external documentation.
* Error messages shown to the user must be written in plain language, not technical error codes.
* The application must be usable on both desktop and mobile browser screen sizes (responsive design).

## 6.5 Maintainability

* The codebase must be split into clearly separated frontend and backend directories.
* All database schema changes must be managed through Alembic migration files, not applied manually.
* Environment-specific configuration (development, production) must be handled through separate environment variable files.

## 6.6 Rate Limiting and API Cost Controls

Because recipe generation and photo scanning involve paid LLM API calls, the system must enforce usage limits to prevent unexpected costs from abuse, bugs, or viral traffic.

* All LLM-dependent endpoints — recipe generation and photo scanning — require authentication. Unauthenticated requests to these endpoints must be rejected with a 401 response before any LLM call is made.
* Recipe generation limit: a maximum of 10 requests per user per calendar day across both Pantry-Based mode and General Browse mode combined.
* Photo scan limit: a maximum of 3 new scan sessions per user per calendar day. Rescan attempts within an existing session (up to 2 per session) do not count toward this limit.
* When a user reaches their daily limit for either endpoint, the system must return a clear message stating the limit and when it resets, rather than a generic error.
* Usage counts are tracked in the api\_usage table (see Section 8.6) and reset at midnight UTC.
* An external monthly spend cap must be configured in the OpenAI dashboard as a hard backstop. This cap operates independently of the per-user limits and prevents any billing surprise if the application-level limits have a bug.

# 7. System Architecture & Technology Stack

## 7.1 Architecture Overview

PantryChef follows a standard client-server architecture. The frontend is a single page React application served as static files. The backend is a Python REST API that handles all business logic, database access, LLM communication, and background scheduling. The database is a managed PostgreSQL instance.

**Request Flow**

* Browser requests the React app from CloudFront (CDN) which serves static files from S3.
* The React app makes API calls to the FastAPI backend running on an EC2 instance.
* The FastAPI backend reads from and writes to an RDS PostgreSQL database.
* For LLM features, the backend calls the OpenAI API over HTTPS.
* The background scheduler runs inside the FastAPI process on EC2 and calls AWS SES to send alert emails.

## 7.2 Technology Choices

| **Layer** | **Technology** | **Notes** |
| --- | --- | --- |
| Frontend | React (Vite) + React Router + TailwindCSS | Vite for fast local development; Tailwind for styling without a heavy framework |
| Backend | Python 3.11 + FastAPI | Async support; auto-generated API docs via /docs; Python aligns with AI integration work |
| ORM & Migrations | SQLAlchemy + Alembic | SQLAlchemy for query building; Alembic to version-control schema changes |
| Database | PostgreSQL 15 | Relational model suits the data; widely supported on AWS RDS |
| AI / Vision | OpenAI GPT-4o | Single model handles both image understanding (pantry scan) and text generation (recipes) |
| Background Jobs | APScheduler (AsyncIOScheduler) | Runs inside the FastAPI process; no separate worker infrastructure needed for MVP |
| Email | boto3 SES client | AWS SDK for Python; SES is reliable and low cost for transactional email |
| Authentication | python-jose (JWT) + passlib (bcrypt) | Standard Python libraries for token signing and password hashing |

## 7.3 AWS Infrastructure

| **Service** | **What It Is** | **How PantryChef Uses It** |
| --- | --- | --- |
| EC2 | A virtual server in the cloud | Hosts the FastAPI backend. The APScheduler job runs within the same process. |
| RDS | Managed relational database service | Hosts the PostgreSQL database. AWS handles backups, patching, and availability. |
| S3 | Cloud object storage | Stores the built React application as static files that can be served as a website. |
| CloudFront | Content delivery network | Sits in front of S3 to serve the React app over HTTPS with low latency. |
| SES | Managed email sending service | Used by the backend to send expiry alert emails to users. |
| IAM | Identity and access management | Assigns a role to the EC2 instance so it can call SES and RDS without storing credentials in code. |
| ACM | Certificate Manager | Issues and manages the HTTPS certificate for the CloudFront distribution. |

# 8. Database Design

The following tables represent the core data model. Column types use PostgreSQL notation.

## 8.1 users

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY | Generated on insert |
| name | VARCHAR(100) |  |
| email | VARCHAR(255) UNIQUE |  |
| password\_hash | VARCHAR(255) | bcrypt hash; never store plaintext |
| dietary\_pref | VARCHAR(50) | e.g. vegetarian, vegan, omnivore |
| nutrition\_goal | VARCHAR(50) | e.g. high-protein, low-carb, balanced |
| allergies | TEXT[] | Array of allergy strings |
| spice\_tolerance | VARCHAR(20) | mild / medium / hot / very-hot |
| cuisine\_prefs | TEXT[] | Array of preferred cuisine strings |
| alert\_enabled | BOOLEAN | Default TRUE |
| alert\_threshold\_days | SMALLINT | Default 3; range 1–7 |
| alert\_time | TIME | Default 08:00; user's local preferred time |
| alert\_channel | VARCHAR(10) | email | sms | push | all — default email |
| created\_at | TIMESTAMPTZ | Set on insert |

## 8.2 pantry\_items

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY |  |
| user\_id | UUID REFERENCES users | Foreign key to users table |
| name | VARCHAR(150) | Normalised item name, e.g. spinach |
| category | VARCHAR(50) | vegetable / dairy / grain / protein / condiment / other |
| quantity | DECIMAL(10,2) |  |
| unit | VARCHAR(30) | grams / pieces / ml / litres / etc. |
| expiry\_date | DATE | User-entered or AI-estimated |
| is\_ai\_estimated | BOOLEAN | TRUE if expiry was inferred by LLM |
| is\_used | BOOLEAN | Soft delete flag; default FALSE |
| added\_at | TIMESTAMPTZ | Set on insert |

## 8.3 shelf\_life\_cache

Stores previously inferred shelf-life results to avoid repeated LLM calls for common items.

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY |  |
| item\_name\_normalised | VARCHAR(150) UNIQUE | Lowercased, stripped item name used as lookup key |
| shelf\_life\_days | SMALLINT | Estimated days from LLM |
| cached\_at | TIMESTAMPTZ | For cache invalidation if needed |

## 8.4 saved\_recipes

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY |  |
| user\_id | UUID REFERENCES users |  |
| title | VARCHAR(200) |  |
| description | TEXT | Short summary from LLM |
| cook\_time\_minutes | SMALLINT |  |
| servings | SMALLINT |  |
| ingredients | JSONB | Array of { name, quantity, unit } |
| steps | JSONB | Ordered array of instruction strings |
| nutrition\_per\_serving | JSONB | { calories, protein\_g, carbs\_g, fat\_g, fibre\_g } |
| allergens\_present | TEXT[] | Allergen strings identified in this recipe |
| allergen\_warning | BOOLEAN | TRUE if any user allergy matched allergens\_present |
| tags | TEXT[] | Descriptive tags |
| rating | SMALLINT | 1 = liked, -1 = disliked, NULL = unrated |
| created\_at | TIMESTAMPTZ |  |

## 8.5 shopping\_list\_items

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY |  |
| user\_id | UUID REFERENCES users |  |
| name | VARCHAR(150) |  |
| quantity | DECIMAL(10,2) |  |
| unit | VARCHAR(30) |  |
| is\_purchased | BOOLEAN | Default FALSE; set TRUE when user marks as bought |
| added\_at | TIMESTAMPTZ |  |

## 8.6 api\_usage

Tracks daily LLM API usage per user. Used to enforce rate limits on recipe generation and photo scanning without blocking legitimate use. One row per user per endpoint type per calendar day.

| **Column** | **Type** | **Notes** |
| --- | --- | --- |
| id | UUID PRIMARY KEY |  |
| user\_id | UUID REFERENCES users |  |
| endpoint\_type | VARCHAR(20) | recipe\_generate | photo\_scan |
| usage\_date | DATE | Calendar date (UTC). Resets daily. |
| count | SMALLINT | Number of calls made today for this endpoint type |
| UNIQUE | (user\_id, endpoint\_type, usage\_date) | Ensures one row per user per type per day; use INSERT ... ON CONFLICT DO UPDATE to increment |

Daily limits enforced via this table: recipe\_generate max 10, photo\_scan max 3. Rescan attempts within a session are tracked in application memory and do not write to this table.

# 9. API Design

All endpoints follow REST conventions. All routes except /auth/\* require a valid Authorization: Bearer <token> header. Request and response bodies use JSON. Path parameters use the {id} notation standard in FastAPI.

## 9.1 Authentication

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| POST | /auth/register | Create account. Body: name, email, password. Returns user id. |
| POST | /auth/login | Authenticate. Body: email, password. Returns JWT access token. |

## 9.2 User Profile

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| GET | /users/me | Fetch the authenticated user's profile and preferences. |
| PUT | /users/me | Update profile fields. Partial updates accepted. |

## 9.3 Pantry

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| GET | /pantry | Return all active (non-used) pantry items for the user. |
| POST | /pantry/scan | Accept image (base64). Call GPT-4o Vision. Return detected items list for user confirmation. |
| POST | /pantry/batch | Save multiple confirmed items in one request. Runs shelf-life inference for items without expiry. |
| POST | /pantry | Add a single item manually. Runs shelf-life inference if expiry omitted. |
| PUT | /pantry/{id} | Update a pantry item's fields. |
| DELETE | /pantry/{id} | Delete a pantry item (hard delete). |
| POST | /pantry/{id}/used | Mark item as used (soft delete — sets is\_used = true). |

## 9.4 Recipes

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| POST | /recipes/suggest | Generate pantry-based recipe suggestions. Body: { prioritise\_expiring: bool }. |
| POST | /recipes/browse | Generate general recipes. Body: { mood, cuisine, notes }. |
| GET | /recipes/saved | Fetch user's saved recipe book. |
| POST | /recipes/saved | Save a recipe. Body: full recipe JSON object. |
| PUT | /recipes/saved/{id}/rating | Update rating. Body: { rating: 1 | -1 }. |
| DELETE | /recipes/saved/{id} | Remove a recipe from the saved book. |

## 9.5 Shopping List

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| GET | /shopping-list | Return all unpurchased shopping list items for the user. |
| POST | /shopping-list | Add item(s) to the list. Accepts single object or array. |
| POST | /shopping-list/{id}/purchased | Mark as purchased and add to pantry. Body: { quantity, unit, expiry\_date? }. |
| DELETE | /shopping-list/{id} | Remove item from the list. |

## 9.6 Alerts

| **Method** | **Path** | **Description** |
| --- | --- | --- |
| GET | /alerts/settings | Fetch current alert configuration for the user. |
| PUT | /alerts/settings | Update alert configuration. Body: { enabled, threshold\_days, alert\_time, channel }. |
| POST | /pantry/{id}/used | Mark a pantry item as used. Called from email action links via a short-lived token. |
| POST | /pantry/{id}/discard | Discard a pantry item. Called from email action links via a short-lived token. |

# 10. Scope Boundary

## 10.1 Version 1 — Web Application (This Document)

| **Feature** | **Included** |
| --- | --- |
| User registration, login, and profile with dietary / allergy / spice / cuisine preferences | Yes |
| Photo-based pantry entry — one photo captures multiple items (GPT-4o Vision) | Yes |
| Rescan flow with manual entry fallback after 2 failed rescans | Yes |
| Manual pantry item entry (always available as fallback) | Yes |
| AI shelf-life inference for items without an expiry date | Yes |
| Shelf-life result caching to reduce LLM calls | Yes |
| Pantry dashboard with colour-coded expiry status | Yes |
| Items remain in pantry past expiry until user explicitly acts | Yes |
| Pantry-based recipe recommendations with GPT-4o | Yes |
| Session-level filters on recipe requests (cuisine, health mode, meal type) | Yes |
| General recipe browse (not constrained to pantry) | Yes |
| Nutrition per serving on every recipe (LLM-estimated) | Yes |
| Allergen detection and server-side safety check per recipe | Yes |
| Save and rate recipes | Yes |
| Daily expiry alert emails with Mark as Used and Discard actions | Yes |
| Shopping list with one-click pantry transfer on purchase | Yes |
| Per-user rate limits: 10 recipe requests/day, 3 scan sessions/day | Yes |
| AWS deployment: EC2, RDS, S3, CloudFront, SES | Yes |
| Analytics dashboard (food waste tracking, streak counter) | Deferred |

## 10.2 Version 2 — Mobile Application (Future)

If the project is extended to a mobile application, the following approach is recommended. This is not in scope for Version 1.

* Framework: React Native with Expo. This allows the same React knowledge to be reused and produces apps for both iOS and Android from a single codebase.
* Distribution: For development and portfolio demonstration, the Expo Go app or an Expo-published web preview is sufficient. Publishing to the Apple App Store or Google Play Store requires developer accounts and an app review process, which is optional.
* Notifications: Mobile apps can deliver expiry alerts via native push notifications (Expo Notifications) rather than email. SMS delivery via Twilio is also available as an option.
* The database schema already includes an alert\_channel column to support email, push, sms, or all — so no schema change is required when this phase is built.
* Backend API: No changes to the backend are required. The React Native app consumes the same REST API as the web frontend.

## 10.3 Permanently Out of Scope

* Barcode scanning for product entry.
* Integration with grocery stores, delivery services, or price comparison.
* Multi-user or shared-household pantry.
* Social features such as sharing recipes or following other users.
* Verified nutritional data from a certified nutritional database (all values in Version 1 are LLM-estimated approximations).