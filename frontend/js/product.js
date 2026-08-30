import { api } from "./api.js";
import { requireAuth } from "./auth.js";
import { escapeHtml, formatMoney } from "./utils.js";

const container = document.querySelector("#productDetail");

function readProductId() {
  const params = new URLSearchParams(window.location.search);
  const id = Number(params.get("id"));
  return Number.isInteger(id) && id > 0 ? id : null;
}

function renderProduct(product) {
  const quantity = Number(product.stock_quantity) || 0;
  const inStock = quantity > 0 && product.status !== "inactive";

  const stockMarkup = inStock
    ? `<span class="badge badge-success">In stock · ${quantity} available</span>`
    : `<span class="badge badge-danger">Out of stock</span>`;

  container.innerHTML = `
    <div class="product-detail-card">
      <div class="product-detail-image">Product image</div>

      <div class="product-detail-info">
        <span class="eyebrow">Product</span>
        <h1>${escapeHtml(product.product_name)}</h1>

        <div class="price">${formatMoney(product.price)}</div>

        <p class="product-detail-desc">${escapeHtml(product.description || "No description available.")}</p>

        <div class="stock-row">${stockMarkup}</div>

        <div class="form-group">
          <label for="quantityInput">Quantity</label>
          <div class="qty-control">
            <button type="button" class="qty-button" id="qtyDown" aria-label="Decrease quantity">−</button>
            <input id="quantityInput" type="number" min="1" max="${quantity || 1}" value="1" aria-label="Quantity">
            <button type="button" class="qty-button" id="qtyUp" aria-label="Increase quantity">+</button>
          </div>
        </div>

        <div class="product-detail-actions">
          <button class="button button-primary" type="button" id="addToCartButton" ${inStock ? "" : "disabled"}>
            ${inStock ? "Add to Cart" : "Unavailable"}
          </button>
          <a class="button button-secondary" href="./products.html">Back to products</a>
        </div>

        <p id="productMessage" class="muted"></p>
      </div>
    </div>
  `;

  const input = document.querySelector("#quantityInput");
  const max = quantity || 1;

  document.querySelector("#qtyDown").addEventListener("click", () => {
    input.value = Math.max(1, Number(input.value) - 1);
  });

  document.querySelector("#qtyUp").addEventListener("click", () => {
    input.value = Math.min(max, Number(input.value) + 1);
  });

  input.addEventListener("change", () => {
    const value = Math.floor(Number(input.value));
    input.value = Number.isFinite(value) ? Math.min(max, Math.max(1, value)) : 1;
  });

  document.querySelector("#addToCartButton").addEventListener("click", async (event) => {
    const button = event.currentTarget;

    if (!requireAuth()) return;

    button.disabled = true;

    try {
      const qty = Math.max(1, Math.floor(Number(input.value)) || 1);
      await api.cart.addItem(product.id, qty);
      showMessage(`Added to cart (qty ${qty}).`, "success");
    } catch (error) {
      showMessage(error.message || "Could not add to cart.", "error");
      button.disabled = false;
    }
  });
}

function showMessage(text, type = "success") {
  const node = document.querySelector("#productMessage");
  if (!node) return;
  node.textContent = text;
  node.className = type === "error" ? "alert alert-error" : "alert alert-success";
}

async function init() {
  const id = readProductId();

  if (!id) {
    container.innerHTML = `
      <div class="empty-state">
        <h2>Product not found</h2>
        <p class="muted">No product was specified in the URL.</p>
        <a class="button button-secondary" href="./products.html">Continue shopping</a>
      </div>
    `;
    return;
  }

  try {
    const product = await api.products.get(id);
    renderProduct(product);
  } catch (error) {
    container.innerHTML = `
      <div class="empty-state">
        <h2>Could not load this product</h2>
        <p class="muted">${escapeHtml(error.message)}</p>
        <a class="button button-secondary" href="./products.html">Browse all products</a>
      </div>
    `;
  }
}

init();