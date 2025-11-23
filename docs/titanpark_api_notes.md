````markdown
# TitanPark Parking System – API Cheat Sheet

Backend repo: `Devilfish281/titanpark-parking-system` (FastAPI)
This document summarizes the available API endpoints, their purposes, methods, parameters, and example requests/responses.

---

## Base URLs

- **Local dev (FastAPI default)**

  - `http://127.0.0.1:8000/`
  - `http://localhost:8000/` (equivalent)

- **Interactive docs (auto-generated OpenAPI)**

  - `http://127.0.0.1:8000/docs` (Swagger UI)

- **Root redirect**
  - `GET /` → redirects to `/docs`

> **Note:** The backend currently exposes parking data, vehicles, and listings.  
> It does **not** provide `/auth/login`, `/lots`, or `/reservations` endpoints; those would need to be implemented in other services or future versions.

---

## 1. Parking Data

### 1.1 GET `/parking_data/all`

**Purpose:**  
Return JSON with **all parking structures** and their live availability / pricing.

**Method:**  
`GET`

**URL:**  
`GET {BASE_URL}/parking_data/all`

**Path / query params:**  
None.

**Shape of the response:**  
The backend returns a **dictionary (map)**, not a list.  
The keys are structure IDs with underscores (for example `"Nutwood_Structure"`), and each value is an object with stats.

**Example request (curl):**

```bash
curl "{BASE_URL}/parking_data/all"
```
````

**Example response (illustrative):**

```json
{
  "Nutwood_Structure": {
    "name": "Nutwood Structure",
    "total": 2504,
    "available": 350,
    "perc_full": 86.02,
    "price_in_cents": 250
  },
  "State_College_Structure": {
    "name": "State College Structure",
    "total": 1373,
    "available": 500,
    "perc_full": 63.57,
    "price_in_cents": 200
  },
  "Eastside_North": {
    "name": "Eastside North",
    "total": 1880,
    "available": 420,
    "perc_full": 77.66,
    "price_in_cents": 230
  },
  "Eastside_South": {
    "name": "Eastside South",
    "total": 1242,
    "available": 310,
    "perc_full": 75.04,
    "price_in_cents": 220
  }
}
```

- `total` – total spaces in that structure (int)
- `available` – current available spaces (int)
- `perc_full` – how full it is **as a percentage** (float, 0.0–100.0)
- `price_in_cents` – dynamic price in cents (int)
- `name` – human-readable structure name with spaces

The test suite expects:

- keys: `"Nutwood_Structure"`, `"State_College_Structure"`, `"Eastside_North"`, `"Eastside_South"`
- types: `available` (int), `total` (int), `perc_full` (float), `price_in_cents` (int), `name` (string)

---

### 1.2 GET `/parking_data/{struct_name}`

**Purpose:**
Return JSON with **occupancy details for a single structure**.

**Method:**
`GET`

**URL pattern:**
`GET {BASE_URL}/parking_data/{struct_name}`

**Path params:**

- `struct_name` – string; **ID-style name with underscores**, like:

  - `"Nutwood_Structure"`
  - `"State_College_Structure"`
  - `"Eastside_North"`
  - `"Eastside_South"`

> The backend uses the underscore version as the key, not the spaced name.
> So you call `/parking_data/Nutwood_Structure`, not `/parking_data/Nutwood%20Structure`.

**Example request (curl):**

```bash
curl "{BASE_URL}/parking_data/Nutwood_Structure"
```

**Example response (illustrative):**

```json
{
  "name": "Nutwood Structure",
  "total": 2504,
  "available": 350,
  "perc_full": 86.02,
  "price_in_cents": 250
}
```

If you call it with a structure that doesn’t exist (for example `"Fake_Structure"`), the API returns:

- HTTP status: `422 Unprocessable Entity`

---

## 2. Vehicles

The backend’s vehicle model (from Postgres / Alembic) looks like:

- `id` – UUID (primary key)
- `user_id` – text
- `make` – text (for example `"Volkswagen"`)
- `model` – text (for example `"Jetta"`)
- `year` – integer
- `color` – text
- `license_plate` – text, unique

### 2.1 POST `/add_vehicle`

**Purpose:**
Add a **vehicle** record for a user (idempotent on license plate: if the plate exists, it updates instead of creating a duplicate).

**Method:**
`POST`

**URL:**
`POST {BASE_URL}/add_vehicle`

**How input is sent (current backend):**
The implementation expects **query parameters**, not a JSON body.
The tests call it like: `POST /add_vehicle?user_id=...&make=...`

**Query parameters:**

- `user_id` – string; user’s ID
- `make` – string; for example `"Volkswagen"`
- `model` – string; for example `"Jetta"`
- `year` – integer; for example `2014`
- `color` – string; for example `"red"`
- `license_plate` – string; plate number; must be unique

**Example request (curl):**

```bash
curl -X POST "{BASE_URL}/add_vehicle" \
  -G \
  --data-urlencode "user_id=testuser123" \
  --data-urlencode "make=Volkswagen" \
  --data-urlencode "model=Jetta" \
  --data-urlencode "year=2014" \
  --data-urlencode "color=red" \
  --data-urlencode "license_plate=8ABC123"
```

**Example success response:**

```json
{
  "vehicle_uuid": "4d285587-bd2b-4a5f-bb0c-2b28c742f63a"
}
```

If validation fails (e.g., missing fields or wrong types), the tests allow:

- HTTP status: `400` or `422`

---

### 2.2 GET `/get_user_vehicles`

**Purpose:**
Return **all vehicles** registered to a given user.

**Method:**
`GET`

**URL:**
`GET {BASE_URL}/get_user_vehicles`

**Query parameters:**

- `user_id` – string; user’s ID.

**Example request (curl):**

```bash
curl "{BASE_URL}/get_user_vehicles?user_id=testuser123"
```

**Shape of the response:**
The backend returns a **dictionary keyed by vehicle UUID**, not a list.

**Example response (illustrative):**

```json
{
  "4d285587-bd2b-4a5f-bb0c-2b28c742f63a": {
    "make": "Volkswagen",
    "model": "Jetta",
    "year": 2014,
    "color": "red",
    "license_plate": "8ABC123"
  },
  "7ea4153e-819f-4d87-8b9a-48fd66b8b7d0": {
    "make": "Audi",
    "model": "A7",
    "year": 2025,
    "color": "white",
    "license_plate": "7XYZ999"
  }
}
```

If the user has no vehicles, the tests allow:

- `{}` (empty object) or `[]` (empty list)

---

### 2.3 POST `/delete_vehicle`

**Purpose:**
Delete a specific vehicle from the database based on its `vehicle_id` (UUID).

**Method:**
`POST` _(not DELETE in this codebase)_

**URL:**
`POST {BASE_URL}/delete_vehicle`

**Query parameters:**

- `vehicle_id` – string, UUID of the vehicle to delete

**Example request (curl):**

```bash
curl -X POST "{BASE_URL}/delete_vehicle" \
  -G \
  --data-urlencode "vehicle_id=4d285587-bd2b-4a5f-bb0c-2b28c742f63a"
```

**Example response:**

```json
{
  "msg": "Deleted vehicle successfully"
}
```

If something goes wrong (e.g., DB error), you get HTTP 500 with an error message.

---

## 3. Listings

The listing table (from migrations) has:

- `id` – UUID (primary key)
- `user_id` – text
- `post_date` – timestamp (default `now()`)
- `price` – integer (e.g., price in cents or whole units)
- `structure_id` – integer (foreign key → `parking_structure.id`)
- `floor` – integer
- `vehicle_id` – UUID (foreign key → `vehicle.id`)
- `comment` – text

### 3.1 POST `/add_listing`

**Purpose:**
Create a **parking spot listing** offered by a user.

**Method:**
`POST`

**URL:**
`POST {BASE_URL}/add_listing`

**How input is sent (current backend):**
Again, as **query parameters**, not JSON.

**Query parameters:**

- `user_id` – string; listing owner
- `price` – integer; must be **≥ 0** (if `< 0`, API returns `400` or `422`)
- `structure_id` – integer; matches an existing `parking_structure.id`
- `floor` – integer; floor number in the structure
- `vehicle_id` – string UUID; must reference an existing `vehicle.id`
- `comment` – string; free text

**Example request (curl):**

```bash
curl -X POST "{BASE_URL}/add_listing" \
  -G \
  --data-urlencode "user_id=testuser123" \
  --data-urlencode "price=100" \
  --data-urlencode "structure_id=1" \
  --data-urlencode "floor=3" \
  --data-urlencode "vehicle_id=4d285587-bd2b-4a5f-bb0c-2b28c742f63a" \
  --data-urlencode "comment=Close to elevator"
```

**Example success response:**

```json
{
  "listing_uuid": "c0b6b9b4-5ea3-4f3e-bcf1-5db5bb85bf6a"
}
```

If `price < 0`, tests expect a `400` or `422` response code.

---

### 3.2 GET `/get_listings`

**Purpose:**
Return **all current listings** in the system (not just one user’s listings).

**Method:**
`GET`

**URL:**
`GET {BASE_URL}/get_listings`

**Query parameters:**
None in the current implementation.
The backend returns **every listing**, and the caller can filter client-side by `user_id` if needed.

**Shape of the response:**
The backend returns a **dictionary keyed by listing UUID**.

Each value contains:

- `user_id`
- `post_date` (timestamp string)
- `price`
- `structure_name` (joined from `parking_structure`)
- `floor`
- `vehicle` object:

  - `make`
  - `model`
  - `year`
  - `color`
  - `license_plate`

- `comment`

**Example response (illustrative):**

```json
{
  "c0b6b9b4-5ea3-4f3e-bcf1-5db5bb85bf6a": {
    "user_id": "testuser123",
    "post_date": "2025-11-21T10:15:32.123456",
    "price": 100,
    "structure_name": "Nutwood Structure",
    "floor": 2,
    "vehicle": {
      "make": "Volkswagen",
      "model": "Jetta",
      "year": 2014,
      "color": "Red",
      "license_plate": "SAFJLK212"
    },
    "comment": "This is a comment for listing 1"
  },
  "d13bf881-913c-4b7d-a1c8-6b0ad621e0f2": {
    "user_id": "testuser456",
    "post_date": "2025-11-21T10:16:05.000000",
    "price": 150,
    "structure_name": "State College Structure",
    "floor": 1,
    "vehicle": {
      "make": "Ford",
      "model": "Mustang",
      "year": 2020,
      "color": "Black",
      "license_plate": "LKSJFD193"
    },
    "comment": "This is a comment for listing 2"
  }
}
```

---

## 4. Quick Summary (What Exists vs. What’s Missing)

**Implemented endpoints (in this backend):**

- `GET /` → redirects to `/docs`
- `GET /parking_data/all`
- `GET /parking_data/{struct_name}` (keys like `"Nutwood_Structure"`)
- `POST /add_vehicle`
- `GET /get_user_vehicles`
- `POST /delete_vehicle` _(note: POST, not DELETE)_
- `POST /add_listing`
- `GET /get_listings` _(returns all listings; filter by `user_id` client-side if needed)_

**Not present in this backend:**

- `POST /auth/login`
- `GET /lots`
- `GET /lots/:id/spots`
- `POST /reservations`
- `PATCH /reservations/:id`

> For exact field names and response schemas:
> Run the backend and visit `http://127.0.0.1:8000/docs`.

---

## 5. Tiny Front-end mapping (React / Flutter)

Simple mental model of **screens → API calls** (you can rename these in your UI).

- **Parking Overview / Dashboard screen**

  - `GET /parking_data/all` – show all structures with live occupancy and pricing.
  - Optionally: `GET /parking_data/{struct_name}` – when the user taps a specific structure tile.

- **My Vehicles screen**

  - `GET /get_user_vehicles?user_id=...` – load the user’s vehicles.
  - `POST /add_vehicle` – add or update a vehicle (idempotent by `license_plate`).
  - `POST /delete_vehicle` – delete a vehicle by `vehicle_id`.

- **My Listings screen**

  - `GET /get_listings` – load all listings, then filter client-side by the current `user_id`.
  - `POST /add_listing` – create a new listing tied to a specific `vehicle_id` and `structure_id`.

- **Browse Listings / Marketplace screen (optional)**

  - `GET /parking_data/all` – for context about structure names and capacity.
  - `GET /get_listings` – show available listings; filter or sort on the frontend.

In **React**, these map to routes/components like:
`<ParkingOverviewPage />`, `<MyVehiclesPage />`, `<MyListingsPage />` calling these endpoints with `fetch` or `axios`.

In **Flutter**, they map to screens like:
`ParkingOverviewScreen`, `MyVehiclesScreen`, `MyListingsScreen` using `http`, `dio`, or another HTTP client.

---

```

```
