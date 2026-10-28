# Product Description Analyzer frontend

Standalone Angular frontend for the Product Description Analyzer mini project.

## Run locally

From this directory:

```powershell
npm install
npm start
```

Open `http://localhost:4200`. The development server proxies `/api` requests to `http://127.0.0.1:8000`.

## Analyzer API contract

The frontend expects the backend to implement `POST /api/analyze` and accept:

```json
{
  "product_name": "Everyday Carry Tote",
  "category": "Accessories",
  "target_audience": "Daily commuters",
  "description": "A durable tote with room for your daily essentials.",
  "tone": "Persuasive"
}
```

The response shape is:

```json
{
  "score": 82,
  "summary": "A clear foundation with room to make the benefits more specific.",
  "strengths": ["Names the product type clearly"],
  "improvements": ["Add material and size details"],
  "optimized_description": "..."
}
```

Start the backend separately on port `8000`. The frontend displays connection and API errors rather than substituting mock AI output.
