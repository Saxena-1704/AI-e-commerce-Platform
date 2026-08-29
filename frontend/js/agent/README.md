# Agent boundary

This folder is intentionally present before the AI agent is implemented.

The future customer agent should operate through commerce capabilities such as:

- searchProducts
- getProduct
- getCart
- addToCart
- updateCart
- removeFromCart
- checkout
- createPayment
- getOrders

The future merchant agent should operate through merchant/admin capabilities such as:

- getDashboardSummary
- getSales
- getTopProducts
- getInventory
- getCustomers
- recommendPromotions

Do not give either agent direct database access.

The agent should call application/business APIs, which enforce the same validation and authorization rules as the human UI.
