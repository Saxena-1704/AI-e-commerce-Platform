# ShopAI Frontend

Plain HTML + CSS + JavaScript frontend for the AI E-Commerce Platform.

## Architecture

The UI is intentionally decoupled from the backend:

HTML pages
  -> page JS
  -> js/api.js
  -> FastAPI
  -> PostgreSQL / Razorpay

`js/api.js` is the frontend's API boundary. Keep backend route knowledge there rather than scattering `fetch()` calls across pages.

Later, a customer AI agent can use the same commerce capabilities instead of manipulating DOM elements.

## Run

From the repository root:

```bash
python -m http.server 5500 --directory frontend
```

Then open:

`http://localhost:5500/`

Do not open the HTML files directly with `file://`; ES modules and API requests work more reliably through a local HTTP server.

## Backend URL

Change only:

`js/config.js`

when FastAPI moves from `http://localhost:8000` to a deployed URL.

## Important

The exact request/response schemas of the existing FastAPI endpoints should be checked against Swagger at:

`http://localhost:8000/docs`

If your register schema uses a field other than `name`, change the payload in `js/auth.js`. If product/category response shapes differ, adjust the normalization in the page JS or, preferably, add normalization inside `js/api.js`.

## Future structure

Recommended next additions:

- `pages/product.html`
- `pages/checkout.html`
- `pages/orders.html`
- `js/cart.js`
- `js/checkout.js`
- `js/orders.js`
- `js/agent/customer-agent.js`
- `merchant/`
- `js/agent/merchant-agent.js`

The agent folders should call capability functions/API modules, not manipulate page DOM directly.
