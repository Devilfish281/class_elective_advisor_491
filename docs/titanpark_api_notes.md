````markdown
# TitanPark Parking System – API Cheat Sheet

Backend repo: `santi224m/titanpark-parking-system` (FastAPI) [GitHub][1]

---

## Base URLs

- **Local dev (FastAPI default)**

  - `http://127.0.0.1:8000/`
  - `http://localhost:8000/` (equivalent)

- **Interactive docs (auto-generated OpenAPI)**
  - `http://127.0.0.1:8000/docs` (Swagger UI)

> **Note:** The backend currently exposes parking data, vehicles, and listings.  
> It does **not** provide `/auth/login`, `/lots`, or `/reservations` endpoints; those will need to be implemented in other services or future versions.

---

## 1. Parking Data

### 1.1 GET `/parking_data/all`

**Purpose:**  
Return JSON with **all parking structures** and their occupancy/availability.

**Method:**  
`GET`

**URL:**  
`GET {BASE_URL}/parking_data/all`

**Path / query params:**  
None.

**Example request (curl):**

```bash
curl "{BASE_URL}/parking_data/all"
```
````

**Example response (illustrative):**

```json
[
  {
    "structure_name": "Nutwood Structure",
    "total_spots": 2000,
    "available_spots": 350,
    "occupied_spots": 1650,
    "occupancy_rate": 0.825
  },
  {
    "structure_name": "State College Structure",
    "total_spots": 1500,
    "available_spots": 500,
    "occupied_spots": 1000,
    "occupancy_rate": 0.667
  }
]
```

> **Note:** Field names and exact schema come from the database / CSV in the backend; use `/docs` to see the precise OpenAPI schema.

---

### 1.2 GET `/parking_data/{structure_name}`

**Purpose:**
Return JSON with **occupancy details for a single structure**.
**Method:**
`GET`

**URL pattern:**
`GET {BASE_URL}/parking_data/{structure_name}`

**Path params:**

- `structure_name` – string; **name** of the structure as used in the dataset
  (e.g., `"Nutwood Structure"`, `"Eastside Parking"`).

**Example request (curl):**

```bash
curl "{BASE_URL}/parking_data/Nutwood%20Structure"
```

**Example response (illustrative):**

```json
{
  "structure_name": "Nutwood Structure",
  "total_spots": 2000,
  "available_spots": 350,
  "occupied_spots": 1650,
  "occupancy_rate": 0.825
}
```

---

## 2. Vehicles

### 2.1 POST `/add_vehicle`

**Purpose:**
Add a **vehicle** record for a user (plate + type + permit).

**Method:**
`POST`

**URL:**
`POST {BASE_URL}/add_vehicle`

**How input is sent (current backend):**
README describes these as **query parameters** (e.g., `?user_id=...&license_plate=...`).

For frontend integration, you can think of the inputs as this logical **JSON shape**:

```json
{
  "user_id": "U1234567",
  "license_plate": "8ABC123",
  "vehicle_type": "Sedan",
  "permit_type": "Student"
}
```

**Query parameters (current implementation):**

- `user_id` – string; user’s ID
- `license_plate` – string; plate number
- `vehicle_type` – string; e.g., `"Sedan"`, `"SUV"`, `"Truck"`
- `permit_type` – string; e.g., `"Student"`, `"Faculty"`, `"Visitor"`

**Example request (curl, using query params as backend expects):**

```bash
curl -X POST "{BASE_URL}/add_vehicle" \
  -G \
  --data-urlencode "user_id=U1234567" \
  --data-urlencode "license_plate=8ABC123" \
  --data-urlencode "vehicle_type=Sedan" \
  --data-urlencode "permit_type=Student"
```

**Example success response (illustrative):**

```json
{
  "message": "Vehicle added successfully",
  "vehicle": {
    "id": 42,
    "user_id": "U1234567",
    "license_plate": "8ABC123",
    "vehicle_type": "Sedan",
    "permit_type": "Student"
  }
}
```

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
curl "{BASE_URL}/get_user_vehicles?user_id=U1234567"
```

**Example response (illustrative):**

```json
[
  {
    "id": 42,
    "user_id": "U1234567",
    "license_plate": "8ABC123",
    "vehicle_type": "Sedan",
    "permit_type": "Student"
  },
  {
    "id": 43,
    "user_id": "U1234567",
    "license_plate": "7XYZ999",
    "vehicle_type": "SUV",
    "permit_type": "Student"
  }
]
```

---

### 2.3 DELETE `/delete_vehicle`

**Purpose:**
Delete a specific vehicle for a user, based on `user_id` and `license_plate`.

**Method:**
`DELETE`

**URL:**
`DELETE {BASE_URL}/delete_vehicle`

**Query parameters:**

- `user_id` – string
- `license_plate` – string

**Example request (curl):**

```bash
curl -X DELETE "{BASE_URL}/delete_vehicle?user_id=U1234567&license_plate=8ABC123"
```

**Example response (illustrative):**

```json
{
  "message": "Vehicle deleted successfully",
  "user_id": "U1234567",
  "license_plate": "8ABC123"
}
```

---

## 3. Listings

### 3.1 POST `/add_listing`

**Purpose:**
Create a **parking spot listing** offered by a user (e.g., subletting a spot).

**Method:**
`POST`

**URL:**
`POST {BASE_URL}/add_listing`

**Backend input style:**
Documented as query parameters in the README.

**Logical JSON shape (for your mental model / frontend):**

```json
{
  "user_id": "U1234567",
  "structure_name": "Nutwood Structure",
  "spot_type": "Covered",
  "price_per_hour": 5.0
}
```

**Query parameters:**

- `user_id` – string
- `structure_name` – string; where the spot is
- `spot_type` – string; e.g., `"Covered"`, `"Uncovered"`, `"EV"`
- `price_per_hour` – number (float)

**Example request (curl, query params):**

```bash
curl -X POST "{BASE_URL}/add_listing" \
  -G \
  --data-urlencode "user_id=U1234567" \
  --data-urlencode "structure_name=Nutwood Structure" \
  --data-urlencode "spot_type=Covered" \
  --data-urlencode "price_per_hour=5.0"
```

**Example response (illustrative):**

```json
{
  "message": "Listing created successfully",
  "listing": {
    "id": 101,
    "user_id": "U1234567",
    "structure_name": "Nutwood Structure",
    "spot_type": "Covered",
    "price_per_hour": 5.0,
    "is_available": true
  }
}
```

---

### 3.2 GET `/get_listings`

**Purpose:**
Return **all listings** created by a given user.

**Method:**
`GET`

**URL:**
`GET {BASE_URL}/get_listings`

**Query parameters:**

- `user_id` – string

**Example request (curl):**

```bash
curl "{BASE_URL}/get_listings?user_id=U1234567"
```

**Example response (illustrative):**

```json
[
  {
    "id": 101,
    "user_id": "U1234567",
    "structure_name": "Nutwood Structure",
    "spot_type": "Covered",
    "price_per_hour": 5.0,
    "is_available": true
  },
  {
    "id": 102,
    "user_id": "U1234567",
    "structure_name": "State College Structure",
    "spot_type": "Uncovered",
    "price_per_hour": 3.5,
    "is_available": false
  }
]
```

---

## 4. Quick Summary (What Exists vs. What’s Missing)

**Implemented endpoints (per backend README):**

- `GET /parking_data/all`
- `GET /parking_data/{structure_name}`
- `POST /add_vehicle`
- `GET /get_user_vehicles`
- `DELETE /delete_vehicle`
- `POST /add_listing`
- `GET /get_listings`

**Not present in this backend (as of the referenced README):**

- `POST /auth/login`
- `GET /lots`
- `GET /lots/:id/spots`
- `POST /reservations`
- `PATCH /reservations/:id`

> For exact field names and response schemas:
> Always double-check `http://127.0.0.1:8000/docs` while the backend is running.

```


```

[1]: https://github.com/santi224m/titanpark-parking-system "GitHub - santi224m/titanpark-parking-system: Handles parking space listings and dynamic pricing"
