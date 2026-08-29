import { api } from "./api.js";

function money(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? `₹${number.toLocaleString("en-IN")}`
    : "Price unavailable";
}

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  return data?.items || data?.products || data?.categories || [];
}

function productCard(product) {
  const id = product.id;
  const name = product.product_name || product.name || "Product";
  const description = product.description || "Explore this product.";
  const price = money(product.price);

  return `
    <article class="product-card">
      <div class="product-image">Product image</div>
      <div class="product-info">
        <div class="product-name">${escapeHtml(name)}</div>
        <div class="product-description">${escapeHtml(description.slice(0, 70))}</div>
        <div class="product-price">${price}</div>
        <div class="product-actions">
          <a class="button secondary" href="./pages/product.html?id=${encodeURIComponent(id)}">View</a>
          <button class="button primary" type="button" disabled>Add</button>
        </div>
      </div>
    </article>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadHome() {
  const productGrid = document.querySelector("#productGrid");
  const categoryGrid = document.querySelector("#categoryGrid");

  try {
    const [productData, categoryData] = await Promise.all([
      api.products.list(),
      api.categories.list(),
    ]);

    const products = normalizeList(productData);
    const categories = normalizeList(categoryData);

    productGrid.innerHTML = products.length
      ? products.slice(0, 4).map(productCard).join("")
      : '<p class="muted">No products available.</p>';

    categoryGrid.innerHTML = categories.length
      ? categories.slice(0, 8).map(category => `
          <a class="category-card" href="./pages/products.html?category=${encodeURIComponent(category.id)}">
            ${escapeHtml(category.category_name || category.name || "Category")}
          </a>
        `).join("")
      : '<p class="muted">No categories available.</p>';
  } catch (error) {
    productGrid.innerHTML = `<p class="muted">Could not load products: ${escapeHtml(error.message)}</p>`;
    categoryGrid.innerHTML = `<p class="muted">Could not load categories.</p>`;
  }
}

document.querySelector("#logoutButton")?.addEventListener("click", () => {
  localStorage.removeItem("access_token");
  window.location.reload();
});

if (localStorage.getItem("access_token")) {
  document.querySelector("#loginLink")?.classList.add("hidden");
  document.querySelector("#registerLink")?.classList.add("hidden");
  document.querySelector("#cartLink")?.classList.remove("hidden");
  document.querySelector("#logoutButton")?.classList.remove("hidden");
}

loadHome();
