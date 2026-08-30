import { api } from "./api.js";
import { requireAuth } from "./auth.js";
import { escapeHtml, formatMoney, normalizeList } from "./utils.js";

const productGrid = document.querySelector("#productGrid");
const categoryGrid = document.querySelector("#categoryGrid");
const message = document.querySelector("#homeMessage");

let featuredProducts = [];

function isInStock(product) {
  return Number(product.stock_quantity) > 0 && product.status !== "inactive";
}

function productCard(product) {
  const inStock = isInStock(product);
  const stockClass = inStock ? "badge-success" : "badge-danger";
  const stockText = inStock ? "In stock" : "Out of stock";

  return `
    <article class="product-card">
      <div class="product-image">Product image</div>
      <div class="product-info">
        <div class="product-name">${escapeHtml(product.product_name)}</div>
        <div class="product-description">${escapeHtml(product.description || "No description available.")}</div>
        <div class="price">${formatMoney(product.price)}</div>
        <div class="product-meta">
          <span class="badge ${stockClass}">${stockText}</span>
        </div>
        <div class="product-actions">
          <a class="button button-secondary" href="./pages/product.html?id=${product.id}">View</a>
          <button class="button button-primary" type="button" data-add="${product.id}" ${inStock ? "" : "disabled"}>
            ${inStock ? "Add to Cart" : "Sold out"}
          </button>
        </div>
      </div>
    </article>
  `;
}

function showMessage(text = "", type = "error") {
  if (!message) return;
  message.textContent = text;
  message.className = text ? (type === "success" ? "alert alert-success" : "alert alert-error") : "muted";
}

productGrid?.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-add]");
  if (!button) return;

  if (!requireAuth()) return;

  const product = featuredProducts.find((entry) => String(entry.id) === button.dataset.add);
  if (!product) return;

  button.disabled = true;

  try {
    await api.cart.addItem(product.id, 1);
    showMessage(`${product.product_name} added to cart.`, "success");
  } catch (error) {
    showMessage(error.message);
    button.disabled = false;
  }
});

async function loadHome() {
  try {
    const [productData, categoryData] = await Promise.all([
      api.products.list(),
      api.categories.list(),
    ]);

    const products = normalizeList(productData);
    const categories = normalizeList(categoryData);

    featuredProducts = products;

    productGrid.innerHTML = products.length
      ? products.slice(0, 4).map(productCard).join("")
      : '<p class="muted">No products available.</p>';

    categoryGrid.innerHTML = categories.length
      ? categories
          .slice(0, 8)
          .map(
            (category) => `
              <a class="category-card" href="./pages/products.html?category=${encodeURIComponent(category.id)}">
                ${escapeHtml(category.category_name || category.name || "Category")}
              </a>
            `
          )
          .join("")
      : '<p class="muted">No categories available.</p>';
  } catch (error) {
    productGrid.innerHTML = `<p class="muted">Could not load products: ${escapeHtml(error.message)}</p>`;
    categoryGrid.innerHTML = `<p class="muted">Could not load categories.</p>`;
  }
}

loadHome();