# Coderr Backend

Coderr is a Django REST Framework (DRF) backend for a freelance developer marketplace.  
It provides authentication, user profiles, offers, orders, reviews and a small set of aggregate
platform statistics.

This repository contains **only the backend**. No frontend code is included.

---

## Tech Stack

- Python 3.11+
- Django 6.0
- Django REST Framework 3.16
- django-cors-headers
- python-dotenv (for loading environment variables from `.env`)
- Pillow (for image fields)
- SQLite as default database (can be replaced with PostgreSQL/MySQL)

---

## Project Structure

```text
core/                  # Django project (settings, urls, wsgi)
  core/settings.py
  core/urls.py
  ...

auth_app/              # Authentication and user profiles
  models.py            # UserProfile
  api/
    serializers.py
    views.py
    urls.py
    permissions.py

coderr_app/            # Marketplace logic
  models.py            # Offer, OfferDetail, Order, Review
  api/
    serializers.py
    views.py
    urls.py
    permissions.py

venv/                  # (optional) Python virtual environment - NOT committed to git
manage.py
```

### Apps Overview

- **auth_app**

  - User registration and login (token based)
  - User profiles with `type` field: `customer` or `business`
  - Profile endpoints for reading and updating

- **coderr_app**
  - Offers and offer details (basic/standard/premium)
  - Orders created from offer details
  - Reviews of business users
  - Aggregated base info endpoint

---

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_REPO_URL> coderr-backend
cd coderr-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> Make sure `Pillow` is installed, otherwise Django will complain about `ImageField`.

---

## Configuration

All basic configuration lives in `core/settings.py`.

For a local development setup you can keep the default settings (SQLite + DEBUG=True),
or provide environment variables for a more advanced setup.

Typical environment variables:

- `DJANGO_SECRET_KEY` – override default secret key
- `DJANGO_DEBUG` – `"True"` or `"False"`
- `DJANGO_ALLOWED_HOSTS` – comma separated list of hosts

If you switch to PostgreSQL or another database, adjust `DATABASES` in `core/settings.py`
and set the required environment variables accordingly.

---

## Database Setup

Run the migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create a superuser (for the Django admin):

```bash
python manage.py createsuperuser
```

---

## Running the Development Server

```bash
python manage.py runserver
```

The API will be available at:

- `http://127.0.0.1:8000/api/`
- Browsable DRF interface for each endpoint

The Django admin is available at:

- `http://127.0.0.1:8000/admin/`

---

## Authentication

The project uses **token-based authentication** via `rest_framework.authtoken`.

### 1. Registration

**POST** `/api/registration/`

Request body:

```json
{
  "username": "exampleUsername",
  "email": "example@mail.de",
  "password": "examplePassword",
  "repeated_password": "examplePassword",
  "type": "customer"
}
```

Response:

```json
{
  "token": "<auth_token>",
  "username": "exampleUsername",
  "email": "example@mail.de",
  "user_id": 1
}
```

### 2. Login

**POST** `/api/login/`

Request body:

```json
{
  "username": "exampleUsername",
  "password": "examplePassword"
}
```

Response:

```json
{
  "token": "<auth_token>",
  "username": "exampleUsername",
  "email": "example@mail.de",
  "user_id": 1
}
```

For authenticated requests, add the token to the `Authorization` header:

```http
Authorization: Token <auth_token>
```

---

## API Overview

All API endpoints are prefixed with `/api/`.

### Authentication & Profiles (`auth_app`)

- **POST** `/api/registration/`  
  Register a new user (customer or business).

- **POST** `/api/login/`  
  Obtain an auth token.

- **GET** `/api/profile/{pk}/`  
  Get a single profile (authenticated only).

- **PATCH** `/api/profile/{pk}/`  
  Update own profile (only profile owner).

- **GET** `/api/profiles/business/`  
  List all business profiles (authenticated).

- **GET** `/api/profiles/customer/`  
  List all customer profiles (authenticated).

---

### Offers & Offer Details (`coderr_app`)

- **GET** `/api/offers/`  
  List offers with pagination, filtering and ordering.  
  Query params:

  - `creator_id`
  - `min_price`
  - `max_delivery_time`
  - `ordering` (`updated_at`, `-updated_at`, `min_price`, `-min_price`)
  - `search`
  - `page_size`

- **POST** `/api/offers/`  
  Create a new offer (business users only).  
  Requires exactly 3 offer details: `basic`, `standard`, `premium`.

- **GET** `/api/offers/{id}/`  
  Retrieve a single offer with links to its details (authenticated).

- **PATCH** `/api/offers/{id}/`  
  Partially update an offer and/or its details (offer owner only).

- **DELETE** `/api/offers/{id}/`  
  Delete an offer (offer owner only).

- **GET** `/api/offerdetails/{id}/`  
  Retrieve a single offer detail (authenticated).

---

### Orders (`coderr_app`)

- **GET** `/api/orders/`  
  List orders where the current user is either `customer_user` or `business_user`  
  (authenticated only).

- **POST** `/api/orders/`  
  Create a new order from an `OfferDetail` (customers only).  
  Request body:

  ```json
  { "offer_detail_id": 1 }
  ```

- **PATCH** `/api/orders/{id}/`  
  Update the `status` (`in_progress`, `completed`, `cancelled`) of an order  
  (business user of that order only).

- **DELETE** `/api/orders/{id}/`  
  Delete an order (staff/admin only). Returns HTTP 204 with no content.

- **GET** `/api/order-count/{business_user_id}/`  
  Get the count of in-progress orders for a specific business user.

- **GET** `/api/completed-order-count/{business_user_id}/`  
  Get the count of completed orders for a specific business user.

---

### Reviews (`coderr_app`)

- **GET** `/api/reviews/`  
  List reviews, with optional filtering and ordering. Query params:

  - `business_user_id`
  - `reviewer_id`
  - `ordering` (`updated_at`, `-updated_at`, `rating`, `-rating`)

- **POST** `/api/reviews/`  
  Create a review for a business user (customers only).  
  One review per `(business_user, reviewer)` pair is allowed.

- **PATCH** `/api/reviews/{id}/`  
  Partially update a review (`rating` and `description` only, review owner only).

- **DELETE** `/api/reviews/{id}/`  
  Delete a review (review owner only, HTTP 204).

---

### Aggregated Base Info (`coderr_app`)

- **GET** `/api/base-info/`  
  Public endpoint (no authentication) providing high-level stats:

  ```json
  {
    "review_count": 10,
    "average_rating": 4.6,
    "business_profile_count": 45,
    "offer_count": 150
  }
  ```

- `average_rating` is calculated across all reviews and rounded to one decimal place.

---

## Coding Guidelines

- Code is PEP 8 compliant.
- One function/method has a single responsibility and stays short.
- No leftover `print()` calls or commented-out code.
- All apps use an `api/` subpackage containing:
  - `serializers.py`
  - `views.py`
  - `urls.py`
  - `permissions.py`

---

## Admin Panel

The Django admin is enabled and can be used to inspect and manage:

- Users
- User profiles
- Offers and offer details
- Orders
- Reviews

After creating a superuser:

```bash
python manage.py createsuperuser
```

You can log in at `http://127.0.0.1:8000/admin/`.

---

## Notes

- Do **not** commit the database file to version control.
- The backend is designed to be consumed by a separate frontend (e.g. React or Vue).
- Make sure to configure CORS appropriately if you expose this API to a browser-based frontend.
