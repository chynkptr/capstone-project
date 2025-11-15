# Routes Documentation for app_modified.py

This document describes all Flask routes defined in `app_modified.py` (project root). It lists each endpoint, expected input (headers/body), how the endpoint processes requests, and the structure of the output JSON responses (happy path and common error responses). Where appropriate, there are Postman/cURL examples and notes about authentication and edge cases.

---

## Summary table

- `GET /` — Service info (no auth)
- `POST /signup` — Create user (body: JSON)
- `POST /login` — Authenticate user, returns JWT (body: JSON)
- `POST /reset-password` — Change password (body: JSON)
- `POST /mole/predict` — Protected: mole image classification (file upload or base64 JSON)
- `GET /health` — Health check (no auth)


---

## Conventions & global notes

- Base URL used in examples: `http://127.0.0.1:8000`
- Date format expected for `dob`: `DD-MM-YYYY` (e.g., `12-11-2025`).
- Protected endpoints expect a JWT in the `Authorization` header with format: `Authorization: Bearer <JWT_TOKEN>`.
- `PREDICTION_THRESHOLD` is set to `0.37`; predictions whose probability > threshold are labeled `Malignant`.
- The app loads a Keras model at startup from `model_mole.keras` (variable `mole_model`). If that model is not available, `/mole/predict` returns 503.
- `preprocess_image` accepts either raw binary image bytes (file upload) or a base64 string (optionally with a data URI prefix like `data:image/jpeg;base64,....`) — the function will detect a string and base64-decode it.


---

## GET /

Description: Root endpoint returning API metadata and available endpoints.

Request
- Method: GET
- URL: `/`
- Headers: none required
- Body: none

Processing
- Returns a small JSON object with a message, version, and list of main endpoints.

Success response (200)
```
{
  "message": "Capstone Medical Prediction API",
  "version": "1.0.0",
  "endpoints": {
    "auth": ["/signup", "/login", "/reset-password"],
    "predictions": ["/mole/predict"]
  }
}
```

Errors: none expected for normal requests.


---

## POST /signup

Description: Create a new user account.

Request
- Method: POST
- URL: `/signup`
- Headers:
  - `Content-Type: application/json`
- Body (JSON):
  - `username` (string, required)
  - `password` (string, required)
  - `dob` (string, required) — format `DD-MM-YYYY`
  - `user_type` (string, optional) — defaults to `user` if omitted

Example JSON body
```
{
  "username": "test1234",
  "password": "test1234",
  "dob": "12-11-2025"
}
```

Processing steps (server-side)
1. `data = request.get_json()` — the route expects JSON. If you send form data instead, `get_json()` will return `None`.
2. Validate required fields `['username','password','dob']` exist in `data`. If any is missing, returns 400 with a helpful message.
3. Check for existing user with the same username — if found, returns 400.
4. Parse `dob` with `datetime.strptime(data['dob'], '%d-%m-%Y')` — if parsing fails, returns 400 and instructs to use `DD-MM-YYYY`.
5. Create `User`, hash the password via `generate_password_hash`, commit to DB.
6. Return a 201 response with created user info.

Success response (201)
```
{
  "message": "User created successfully",
  "user": {
    "id": <integer>,
    "username": "test1234",
    "user_type": "user",
    "dob": "2025-11-12",
    "created_at": "2025-11-12T..."
  }
}
```

Common error responses
- 400 — Missing field: `{ "error": "<field> is required" }`
- 400 — Username already exists: `{ "error": "Username already exists" }`
- 400 — Invalid date format: `{ "error": "Invalid date format. Use DD-MM-YYYY" }`
- 500 — Server/database error with message: `{ "error": "..." }`

How to call from Postman
1. Method: POST, URL: `http://127.0.0.1:8000/signup`
2. In Postman → Body → raw → select `JSON` and paste the example JSON body.
3. Send. Ensure the header `Content-Type: application/json` is present (Postman sets this automatically for raw JSON).

Notes & edge cases
- If you call `/signup` using a browser URL with query parameters (GET), you'll get an error because the endpoint requires POST and expects JSON.


---

## POST /login

Description: Authenticate a user and return a JWT token for protected routes.

Request
- Method: POST
- URL: `/login`
- Headers:
  - `Content-Type: application/json`
- Body (JSON):
  - `username` (string, required)
  - `password` (string, required)

Example JSON body
```
{
  "username": "test1234",
  "password": "test1234"
}
```

Processing steps
1. `data = request.get_json()` — expects JSON.
2. Validate username and password provided; else return 400.
3. Lookup the user by username; verify password with password hash.
4. If valid, generate a JWT token using `jwt.encode({...}, app.config['SECRET_KEY'], algorithm='HS256')`. The payload includes `user_id`, `username`, `user_type`, and `exp` (expiration = now + 1 day).
5. Return 200 with a JSON object containing `message`, `token`, and the `user` object.

Success response (200)
```
{
  "message": "Login successful",
  "token": "<JWT_TOKEN_STRING>",
  "user": {
    "id": <integer>,
    "username": "test1234",
    "user_type": "user",
    "dob": "2025-11-12",
    "created_at": "2025-11-12T..."
  }
}
```

Common error responses
- 400 — Missing credentials: `{ "error": "Username and password are required" }`
- 401 — Invalid credentials: `{ "error": "Invalid credentials" }`
- 500 — Server error with message

How to call from Postman
1. Method: POST, URL: `http://127.0.0.1:8000/login`
2. Body → raw → JSON with username and password.
3. On success, copy the `token` value from the JSON response for use with protected endpoints.


---

## POST /reset-password

Description: Change an existing user's password.

Request
- Method: POST
- URL: `/reset-password`
- Headers: `Content-Type: application/json`
- Body (JSON):
  - `username` (string, required)
  - `old_password` (string, required)
  - `new_password` (string, required)

Example JSON body
```
{
  "username": "test1234",
  "old_password": "test1234",
  "new_password": "newpass123"
}
```

Processing steps
1. Get JSON body and validate required fields.
2. Lookup user by username; if not found return 404.
3. Verify `old_password` using stored hash; if incorrect return 401.
4. Update password hash to new password and commit.
5. Return 200 message on success.

Success response (200)
```
{ "message": "Password updated successfully" }
```

Common error responses
- 400 — Missing fields: `{ "error": "<field> is required" }`
- 404 — User not found: `{ "error": "User not found" }`
- 401 — Invalid old password: `{ "error": "Invalid old password" }`
- 500 — Server/database error

How to call from Postman
- POST to `http://127.0.0.1:8000/reset-password` with raw JSON body as shown.


---

## POST /mole/predict (Protected)

Description: Classify an uploaded mole image as `Benign` or `Malignant` using a preloaded Keras model. This route is protected by JWT — you must include `Authorization: Bearer <token>` header.

Request
- Method: POST
- URL: `/mole/predict`
- Headers:
  - `Authorization: Bearer <JWT_TOKEN>` (required)
  - If sending JSON: `Content-Type: application/json`
  - If uploading file (form-data), Postman will set `Content-Type: multipart/form-data` automatically.

Two supported input formats:

A) File upload (recommended)
- Body → `form-data`
  - Key: `image` (type: File) — choose an image file (JPEG/PNG)

B) Base64 image in JSON
- Body → raw → JSON
  - Field: `image_data` (string) — a base64 string. It may be a data URL such as `data:image/jpeg;base64,<base64>` or just the raw base64 content.

Examples
File upload (form-data):
- `image` (file): my_mole.jpg

JSON base64 example:
```
{
  "image_data": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

Processing steps
1. `token_required` decorator:
   - Reads `Authorization` header.
   - Strips `Bearer ` prefix and decodes the token with `app.config['SECRET_KEY']`.
   - If token missing, invalid, expired, or user not found: returns 401 with message.
   - On success, `current_user` is fetched and passed as the first parameter to the view.
2. Verify model loaded: if `mole_model is None` return 503 with error message.
3. Check input: either `request.files['image']` exists or `request.json['image_data']` exists — otherwise 400.
4. If `image` file present: read binary via `file.read()`.
   If JSON `image_data` present: value is passed into `preprocess_image`.
5. `preprocess_image` behavior:
   - If passed a string, it detects and base64-decodes (also handles data URL prefix by splitting on `,`).
   - Opens image via PIL, converts to RGB if needed, resizes to `(224,224)`, converts to numpy array, normalizes to [0,1], expands dims to shape `(1,224,224,3)`.
6. Model prediction: `mole_model.predict(processed_image, verbose=0)` yields a sigmoid probability (single value per batch item). The code takes `probability = float(prediction_proba[0][0])`.
7. Apply threshold `PREDICTION_THRESHOLD = 0.37`: if `probability > 0.37` -> `prediction_class = 1` (Malignant), else 0 (Benign).
8. Build result JSON with `prediction` label, `probabilities` for both classes, and the `user_id` from the token.

Success response (200)
```
{
  "prediction": "Benign" | "Malignant",
  "probabilities": {
    "Benign": <float>,
    "Malignant": <float>
  },
  "user_id": <integer>
}
```

Example
```
{
  "prediction": "Malignant",
  "probabilities": { "Benign": 0.12, "Malignant": 0.88 },
  "user_id": 3
}
```

Common error responses
- 401 — Token missing or invalid, errors from token decorator:
  - `{ "message": "Token is missing!" }`
  - `{ "message": "Token is invalid!" }`
  - `{ "message": "Token has expired!" }`
- 400 — No image provided: `{ "error": "No image provided" }`
- 400 — If file empty: `{ "error": "No image selected" }`
- 503 — Model not available: `{ "error": "Mole classification model not available" }`
- 500 — Any other server or model error: `{ "error": "..." }`

How to call from Postman (file upload)
1. Ensure you have a valid JWT from `/login`.
2. In Postman, open `/mole/predict` request.
3. Select the `Authorization` tab → Type: `Bearer Token` → paste your token into the `Token` field OR add a header under `Headers`: `Authorization: Bearer <token>`.
4. Body → form-data → add key `image` of type File → choose image file.
5. Send.

How to call from Postman (base64 JSON)
1. Authorization as above.
2. Body → raw → JSON, for example:
```
{
  "image_data": "data:image/png;base64,iVBORw0KGgoAAAANS..."
}
```
3. Send. If you use raw JSON, Postman will set `Content-Type: application/json`.

Notes & edge cases
- If sending raw base64, include only the string (data URL or plain base64). `preprocess_image` will handle both.
- Keep the Authorization header present — otherwise the token decorator will return 401 before any image validation.


---

## GET /health

Description: Simple health check. Not a deep DB connectivity test; returns whether the `db` object exists and whether the model variable `mole_model` is loaded.

Request
- Method: GET
- URL: `/health`
- Headers: none required

Processing
- Returns JSON with keys: `status`, `database`, `mole_model_loaded`, and `timestamp`.

Example response (200)
```
{
  "status": "healthy",
  "database": "connected",   // note: this only checks truthiness of `db`, not an active connection
  "mole_model_loaded": true,
  "timestamp": "2025-11-12T..."
}
```

Notes
- `database` field uses a simple truthiness check: `'connected' if db else 'disconnected'`. It does not attempt a test query, so treat this as a lightweight check.


---

## Error handlers (global)
The application includes several global error handlers defined in `app_modified.py`.

- 404 handler: returns `{ "error": "Endpoint not found" }` with 404 status.
- 500 handler: returns `{ "error": "Internal server error" }` with 500 status.
- 413 handler: returns `{ "error": "File too large" }` with 413 status. The app also sets `MAX_CONTENT_LENGTH` to 16 MB, so uploads larger than that will trigger 413.


---

## Tips, troubleshooting & recommendations

- Always POST JSON with `Content-Type: application/json` for `/signup`, `/login`, and `/reset-password`.
- For `/mole/predict`, prefer form-data file upload (`image` key) to avoid base64-related size and encoding issues.
- Use Postman Authorization → `Bearer Token` to paste the token you received from `/login`. Postman will automatically add the correct header.
- If you see 415 or JSON parsing errors, check that your request has the correct `Content-Type` and that you are sending the expected body format.
- If `/mole/predict` returns 503, the server could not load the model at startup — verify `model_mole.keras` exists and is loadable from the project root.
- `dob` in responses is ISO date (YYYY-MM-DD) because `User.to_dict()` converts date to `isoformat()`.


---

## Appendix — quick cURL examples

Signup
```
curl -X POST http://127.0.0.1:8000/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"test1234","password":"test1234","dob":"12-11-2025"}'
```

Login
```
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test1234","password":"test1234"}'
```

Predict (file upload)
```
curl -X POST http://127.0.0.1:8000/mole/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -F "image=@/path/to/mole.jpg"
```

Predict (base64 JSON)
```
curl -X POST http://127.0.0.1:8000/mole/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"image_data":"data:image/jpeg;base64,/9j/4AAQ..."}'
```


---

If you want, I can:
- add this file to your repository (already created),
- add one-line examples to your README to show how to call the API,
- or generate a Postman collection with example requests for each endpoint.

If you want me to proceed with any of those, tell me which one and I'll add it.
