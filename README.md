# AgenCart

AgenCart is an agentic commerce platform: customers can browse a storefront or use an AI buyer agent to discover products, manage a cart, create checkout sessions, and pay through Razorpay. Merchants get a dashboard and a Merchant Growth Agent that can combine store data with Razorpay data.

## Key features

- Commerce platform with customer authentication, categories, products, carts, orders, merchant views, and checkout.
- Buyer/Customer AI that discovers a merchant through UCP, discovers MCP tools, and uses them to shop.
- Merchant AI for store overview, products, orders, payments, refunds, and settlement questions.
- MCP tools for catalog, cart, checkout, and payment operations.
- UCP discovery through `/.well-known/ucp` and a UCP-compatible shopping profile.
- Razorpay test-mode order creation, browser checkout, signature verification, webhook handling, and payment status tracking.

## Project structure

```text
backend/app/                 FastAPI application, APIs, services, models
backend/app/mcp/             AgenCart MCP server and shopping tools
backend/app/ucp/             UCP profile
backend/app/agent/           Merchant AI and Razorpay MCP client
backend/alembic/             Database migrations
frontend/                    Plain HTML/CSS/ES-module storefront
AI Customer Agent/app/       Customer Agent FastAPI service
AI Customer Agent/web/       Customer Agent web UI
tests/                       Catalog, HTTP MCP, and payment lifecycle tests
uploads/products/            Product images
```

## Prerequisites and environment variables

You need Python, PostgreSQL, a Razorpay test account, and (for AI features) a Groq API key. Install the root dependencies from `requirements.txt`; the Customer Agent has its own `requirements.txt`.

Create `.env` at the repository root. The backend reads these variables:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/ecommerce_db
RAZORPAY_TEST_API_KEY=rzp_test_your_key
RAZORPAY_TEST_KEY_SECRET=your_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
JWT_SECRET_KEY=replace_with_a_long_random_secret
APP_ENV=development
SQL_ECHO=false
FRONTEND_BASE_URL=http://localhost:8000
```

The Merchant AI additionally requires `GROQ_API_KEY` and `GROQ_MODEL`. Its Razorpay MCP client uses the Razorpay test API credentials above. `MERCHANT_API_BASE_URL` is optional and defaults to `http://localhost:8000`.

The Customer Agent service reads its own `.env` from `AI Customer Agent/`:

```env
GROQ_API_KEY=your_groq_key
MERCHANT_API_URL=http://localhost:8000
```

The Customer Agent accepts buyer credentials in its login form; its backend keeps the merchant JWT in a process-local session and does not send the JWT or Groq key to the browser.

## How to start

Run the two FastAPI services in separate terminals.

### 1. Commerce backend

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

The backend serves the API, the storefront, product uploads, UCP discovery, and the AgenCart MCP endpoint.

- API/root: http://localhost:8000/
- Storefront: http://localhost:8000/
- UCP profile: http://localhost:8000/.well-known/ucp
- MCP endpoint: http://localhost:8000/ucp/mcp/
- Database check: http://localhost:8000/db-test

### 2. Example Customer Agent

From the repository root:

```powershell
cd 'AI Customer Agent'
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

Open http://localhost:8100/. The service also exposes http://localhost:8100/health.

## How the system works

1. A customer uses the storefront or Customer Agent.
2. The Customer Agent fetches the merchant UCP profile from `/.well-known/ucp` and extracts the MCP endpoint.
3. It authenticates the buyer through `/auth/login`, then connects to the commerce MCP server with the JWT.
4. MCP tools call the commerce platform’s catalog, cart, checkout, and payment services.
5. Checkout creates an order and a Razorpay payment attempt. The human completes payment in the Razorpay checkout flow.
6. The backend verifies the Razorpay signature/webhook and updates payment, order, and stock state.
7. The merchant dashboard and Merchant AI can inspect store and payment results.

## MCP servers

The repository’s AgenCart MCP server is a FastMCP server mounted inside the backend at `/ucp/mcp/`. It requires an AgenCart bearer JWT and exposes:

- Catalog: `search_catalog`, `lookup_catalog`, `get_product`, `list_categories`
- Cart: UCP cart operations plus `get_customer_cart`, `add_to_cart`, `update_cart_item`, and `remove_from_cart`
- Checkout: `create_checkout`, `get_checkout`, `update_checkout`, `complete_checkout`, and `cancel_checkout`
- Payment: `create_payment` and `get_payment_status`

The Merchant AI also connects to Razorpay’s hosted MCP server at `https://mcp.razorpay.com/mcp` using Basic authentication derived from the Razorpay test credentials. It selects Razorpay tools for orders, payments, refunds, and settlements, then combines them with read-only merchant API tools.

## UCP and Razorpay integration

`backend/app/ucp/profile.py` publishes the `dev.ucp.shopping` service and catalog, cart, and checkout capabilities. The profile advertises the MCP transport and endpoint used by the Customer Agent. Catalog and checkout responses use minor currency units; for INR, amounts are paise.

Razorpay orders are created by the backend in INR. The payment page opens Razorpay Checkout, and the backend verifies the returned signature. Payment webhooks are handled by the payments API. Stock is reduced only after successful payment finalization; failed or duplicate payment events do not reduce stock more than once.

## Example Customer Agent

The Customer Agent demonstrates agent-first shopping without DOM automation. It discovers the merchant dynamically through UCP, discovers authenticated MCP tools, and lets a buyer ask for products, prices, availability, cart changes, checkout, and payment details. Its FastAPI wrapper exposes:

- `POST /api/login`
- `POST /api/logout`
- `POST /api/chat`

## Demo flow

1. Start PostgreSQL and configure `.env`.
2. Start the commerce backend at http://localhost:8000/ and the Customer Agent at http://localhost:8100/.
3. Register a buyer at http://localhost:8000/pages/register.html and log in.
4. Browse products or start the Customer Agent and ask for a product.
5. Add an item to the cart and create checkout.
6. Complete payment with Razorpay test credentials.
7. Inspect the order in the storefront and use the merchant dashboard/agent for store and payment questions.

## Testing and troubleshooting

Run the repository unit tests from the root after installing the root requirements:

```powershell
python -m unittest discover -s tests
```

Useful MCP checks:

```powershell
python tests/test_http_mcp.py
python tests/test_catalog_mcp.py
```

If the backend fails during startup, check `DATABASE_URL`, `JWT_SECRET_KEY`, and the Razorpay test credentials. If AI features fail, check `GROQ_API_KEY`, `GROQ_MODEL`, and the Customer Agent’s `MERCHANT_API_URL`. Open the storefront through http://localhost:8000/ so its API requests resolve correctly.
