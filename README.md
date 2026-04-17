# Profiles API

A FastAPI microservice that aggregates data from three external APIs (Genderize, Agify, Nationalize), classifies it, persists it in a database, and exposes a full CRUD REST API.

---

## Project Structure

```
profiles-api/
├── api/
│   └── main.py       # FastAPI app (Vercel entrypoint)
├── requirements.txt
└── README.md
```

---

## Endpoints

### `POST /api/profiles`
Creates a new profile by calling all three external APIs.  
If the name already exists, returns the existing profile without re-fetching.

**Request body:**
```json
{ "name": "ella" }
```

**Success (201):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DRC",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**Already exists (200):**
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### `GET /api/profiles/{id}`
Returns a single profile by UUID.

**Success (200):** Full profile object (same shape as POST response data).  
**Not found (404):** `{ "status": "error", "message": "Profile not found" }`

---

### `GET /api/profiles`
Returns all profiles. Supports optional case-insensitive filters:

| Query param  | Example              |
|--------------|----------------------|
| `gender`     | `?gender=male`       |
| `country_id` | `?country_id=NG`     |
| `age_group`  | `?age_group=adult`   |

**Success (200):**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    { "id": "...", "name": "emmanuel", "gender": "male", "age": 25, "age_group": "adult", "country_id": "NG" }
  ]
}
```

---

### `DELETE /api/profiles/{id}`
Deletes a profile. Returns **204 No Content** on success.

---

## Processing Rules

| Field              | Source       | Logic                                         |
|--------------------|--------------|-----------------------------------------------|
| `gender`           | Genderize    | Direct                                        |
| `gender_probability` | Genderize  | Direct                                        |
| `sample_size`      | Genderize    | `count` renamed                               |
| `age`              | Agify        | Direct                                        |
| `age_group`        | Agify        | 0–12 → child, 13–19 → teenager, 20–59 → adult, 60+ → senior |
| `country_id`       | Nationalize  | Country with highest probability              |
| `country_probability` | Nationalize | Probability of top country                 |
| `id`               | Generated    | UUID v7                                       |
| `created_at`       | Generated    | UTC ISO 8601                                  |

---

## Error Handling

| Status | Condition |
|--------|-----------|
| `400`  | Missing or empty `name` |
| `422`  | `name` has no alphabetic characters |
| `404`  | Profile not found |
| `502`  | External API returned null/empty data |
| `500`  | Internal server error |

All errors: `{ "status": "error", "message": "..." }`  
502 from external APIs: `{ "status": "502", "message": "Genderize returned an invalid response" }`

---

## Local Development

### Prerequisites
- Python 3.10+

### Setup

```bash
git clone <your-repo-url>
cd profiles-api

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Run (SQLite by default — no setup needed)

```bash
uvicorn api.index:app --reload --port 8000
```

Test:
```bash
# Create a profile
curl -X POST "http://localhost:8000/api/profiles" \
  -H "Content-Type: application/json" \
  -d '{"name": "james"}'

# List all profiles
curl "http://localhost:8000/api/profiles"

# Filter
curl "http://localhost:8000/api/profiles?gender=male&country_id=NG"

# Get by ID
curl "http://localhost:8000/api/profiles/<id>"

# Delete
curl -X DELETE "http://localhost:8000/api/profiles/<id>"
```

---


## CORS

`Access-Control-Allow-Origin: *` is set globally via FastAPI's `CORSMiddleware`.