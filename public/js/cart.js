import { api } from "./api.js";
import { requireAuth } from "./auth.js";
import { runCheckout } from "./checkout.js";
import { escapeHtml, formatMoney, resolveImageUrl } from "./utils.js";

const container = document.querySelector("#cartContainer");

// Enriched line items: backend cart item { id, product_id, quantity } merged
// with the product fetched through api.products.get(product_id).
let cartItems = [];

function lineSubtotal(item) {
  return Number(item.product.price) * Number(item.quantity);
}

function renderEmpty() {
  container.innerHTML = `
    <div class="empty-state">
      <h2>Your cart is empty.</h2>
      <p class="muted">Find something you like and add it to the cart.</p>
      <a class="button button-primary" href="./products.html">Continue Shopping</a>
    </div>
  `;
}

function renderError(text) {
  container.innerHTML = `
    <div class="empty-state">
      <h2>Could not load your cart</h2>
      <p class="muted">${escapeHtml(text)}</p>
      <a class="button button-secondary" href="./products.html">Continue Shopping</a>
    </div>
  `;
}

function showMessage(text, type = "error") {
  const node = document.querySelector("#cartMessage");
  if (!node) return;
  node.textContent = text;
  node.className = type === "success" ? "alert alert-success" : "alert alert-error";
}

function renderLines(items) {
  const rows = items
    .map((item) => {
      const product = item.product;
      const stock = Number(product.stock_quantity) || 1;
      const imageUrl = resolveImageUrl(product.image_url);

      return `
        <div class="cart-row" data-item-id="${item.id}">
          <div class="cart-product">
            <div class="cart-thumb">${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(product.product_name)}">` : "Product"}</div>
            <div>
              <a class="cart-name" href="./product.html?id=${product.id}">
                ${escapeHtml(product.product_name)}
              </a>
              <div class="price">${formatMoney(product.price)}</div>
            </div>
          </div>

          <div class="qty-control">
            <button type="button" class="qty-button" data-action="decrease" aria-label="Decrease quantity">−</button>
            <input
              type="number"
              min="1"
              max="${stock}"
              value="${item.quantity}"
              aria-label="Quantity"
              data-qty
            >
            <button type="button" class="qty-button" data-action="increase" aria-label="Increase quantity">+</button>
          </div>

          <div class="cart-subtotal">${formatMoney(lineSubtotal(item))}</div>

          <button type="button" class="button button-secondary cart-remove" data-action="remove">Remove</button>
        </div>
      `;
    })
    .join("");

  const total = items.reduce((sum, item) => sum + lineSubtotal(item), 0);

  container.innerHTML = `
    <div class="cart-list">${rows}</div>

    <div class="cart-summary">
      <div class="summary-row">
        <span>Total</span>
        <span class="price cart-total">${formatMoney(total)}</span>
      </div>
      <button class="button button-primary full-width" type="button" id="checkoutButton">
        Proceed to Checkout
      </button>
      <a class="text-link" href="./products.html">← Continue shopping</a>
    </div>

    <p id="cartMessage" class="muted"></p>
  `;

  document.querySelector("#checkoutButton").addEventListener("click", handleCheckout);
}

async function loadCart() {
  if (!requireAuth()) return;

  try {
    const cart = await api.cart.get();
    const items = Array.isArray(cart.items) ? cart.items : [];

    const itemsWithProducts = await Promise.all(
      items.map(async (item) => {
        const product = await api.products.get(item.product_id);
        return { ...item, product };
      })
    );

    cartItems = itemsWithProducts;
    renderLines(cartItems);
  } catch (error) {
    renderError(error.message);
  }
}

async function updateQuantity(itemId, requestedQuantity) {
  const item = cartItems.find((entry) => entry.id === itemId);
  if (!item) return;

  const max = Number(item.product.stock_quantity) || 1;
  const next = Math.min(max, Math.max(1, Math.floor(requestedQuantity) || 1));

  try {
    await api.cart.updateItem(itemId, next);
    await loadCart();
  } catch (error) {
    showMessage(error.message);
  }
}

async function removeItem(itemId) {
  try {
    await api.cart.removeItem(itemId);
    await loadCart();
  } catch (error) {
    showMessage(error.message);
  }
}

async function handleCheckout(event) {
  const button = event.currentTarget;
  button.disabled = true;

  try {
    const orderId = await runCheckout();
    showMessage("Payment successful! Taking you to your order...", "success");
    setTimeout(() => {
      window.location.href = `./order.html?id=${orderId}`;
    }, 900);
  } catch (error) {
    showMessage(error.message);
    button.disabled = false;
    // Re-sync in case checkout consumed/rolled back stock or quantities.
    await loadCart();
  }
}

container.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  const row = button?.closest("[data-item-id]");
  if (!button || !row) return;

  const itemId = Number(row.dataset.itemId);
  const qtyInput = row.querySelector("[data-qty]");
  const action = button.dataset.action;

  if (action === "increase") {
    updateQuantity(itemId, Number(qtyInput.value) + 1);
  } else if (action === "decrease") {
    updateQuantity(itemId, Number(qtyInput.value) - 1);
  } else if (action === "remove") {
    removeItem(itemId);
  }
});

container.addEventListener("change", (event) => {
  const input = event.target.closest("[data-qty]");
  const row = input?.closest("[data-item-id]");
  if (!input || !row) return;

  updateQuantity(Number(row.dataset.itemId), Number(input.value));
});

loadCart();
