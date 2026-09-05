# AgenCart Frontend

Plain HTML + CSS + JavaScript (ES modules) frontend for the AI E-Commerce Platform.

## Architecture

The UI is intentionally decoupled from the backend:

```
HTML pages
  -> page JS (js/home.js, js/products.js, js/cart.js, ...)
  -> js/api.js            <- the ONLY place that talks to the backend
  -> FastAPI (localhost:8000)
  -> PostgreSQL / Razorpay
```

`js/api.js` is the frontend's API boundary. Backend route knowledge and the
base URL (`js/config.js`) live there; page code never contains `fetch()` calls
or backend URLs. The Customer Agent uses the same commerce capabilities
through the backend MCP endpoint instead of manipulating page DOM elements.

## Pages

| Page             | Route                            | Module                 |
| ---------------- | -------------------------------- | ---------------------- |
| Home             | `index.html`                     | `js/home.js`           |
| Login            | `pages/login.html`               | `js/auth.js`           |
| Register         | `pages/register.html`            | `js/auth.js`           |
| Products         | `pages/products.html`            | `js/products.js`       |
| Product detail   | `pages/product.html?id=<id>`     | `js/product.js`        |
| Cart + checkout  | `pages/cart.html`                | `js/cart.js` + `js/checkout.js` |
| Order history    | `pages/orders.html`              | `js/orders.js`         |
| Order detail     | `pages/order.html?id=<order_id>` | `js/orders.js`         |

Checkout runs from the cart page: it calls order checkout, creates a Razorpay
payment, opens Razorpay's checkout modal, and verifies the payment signature
(verified server-side), then redirects to the order detail page.

## Run

The storefront is served by the commerce backend. Start FastAPI from the
repository root:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Then open:

```
http://localhost:8000/
```

`backend/app/main.py` serves the API and this frontend from the same FastAPI
process.

## Shared helpers

- `js/auth.js` — `isAuthenticated()`, `requireAuth()`, `logout()`, `initNavbar()`
  (the auth-aware navbar is injected into `<span id="navAuth">` on every page),
  plus login/register form handling.
- `js/utils.js` — `escapeHtml()`, `formatMoney()` (handles Decimal-as-string
  values), `normalizeList()`.

## Backend URL

Change only:

`js/config.js`

when FastAPI moves from `http://localhost:8000` to a deployed URL.
Razorpay credentials come from the backend `.env` (never the frontend).
