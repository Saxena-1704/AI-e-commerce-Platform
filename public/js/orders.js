import { api } from "./api.js";
import { requireAuth } from "./auth.js";
import { escapeHtml, formatMoney } from "./utils.js";

// ---------------------------------------------------------------------------
// Both /orders.html (history) and /order.html?id= (detail) are driven by this
// module. The active page is detected from the container element that exists.
// ---------------------------------------------------------------------------

const ordersList = document.querySelector("#ordersList");
const orderDetail = document.querySelector("#orderDetail");

function statusBadge(status) {
  const tone = status === "paid" ? "badge-success" : "badge-neutral";
  const label = String(status || "unknown").toUpperCase();
  return `<span class="badge ${tone}">${escapeHtml(label)}</span>`;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ----------------------------- Orders history -----------------------------

function renderOrdersList(orders) {
  if (!orders.length) {
    ordersList.innerHTML = `
      <div class="empty-state">
        <h2>No orders yet</h2>
        <p class="muted">When you check out, your orders will appear here.</p>
        <a class="button button-primary" href="./products.html">Start shopping</a>
      </div>
    `;
    return;
  }

  ordersList.innerHTML = `
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Date</th>
            <th>Total</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${orders
            .map(
              (order) => `
                <tr>
                  <td class="order-number">${escapeHtml(order.order_number)}</td>
                  <td class="muted">${formatDate(order.created_at)}</td>
                  <td class="price">${formatMoney(order.total_amount)}</td>
                  <td>${statusBadge(order.status)}</td>
                  <td class="table-actions">
                    <a class="button button-secondary" href="./order.html?id=${order.id}">View</a>
                  </td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

async function initOrdersList() {
  if (!requireAuth()) return;

  try {
    const data = await api.orders.list();
    const orders = Array.isArray(data) ? data : [];
    renderOrdersList(orders);
  } catch (error) {
    ordersList.innerHTML = `
      <div class="empty-state">
        <h2>Could not load your orders</h2>
        <p class="muted">${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

// ----------------------------- Order detail -------------------------------

function renderOrderDetail(order) {
  const items = Array.isArray(order.items) ? order.items : [];

  const rows = items
    .map(
      (item) => `
        <tr>
          <td class="order-product">${escapeHtml(item.product_name)}</td>
          <td>${formatMoney(item.price)}</td>
          <td>${item.quantity}</td>
          <td class="price">${formatMoney(item.total_amount)}</td>
        </tr>
      `
    )
    .join("");

  orderDetail.innerHTML = `
    <div class="order-detail">
      <div class="order-heading">
        <div>
          <span class="eyebrow">Order</span>
          <h1>${escapeHtml(order.order_number)}</h1>
          <p class="muted">Placed on ${formatDate(order.created_at)}</p>
        </div>
        <div class="order-status">${statusBadge(order.status)}</div>
      </div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Price</th>
              <th>Qty</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>

      <div class="order-summary">
        <div class="summary-row"><span>Subtotal</span><span>${formatMoney(order.subtotal)}</span></div>
        <div class="summary-row"><span>Discount</span><span>${formatMoney(order.discount_amount)}</span></div>
        <div class="summary-row"><span>Shipping</span><span>${formatMoney(order.shipping_amount)}</span></div>
        <div class="summary-row"><span>Tax</span><span>${formatMoney(order.tax_amount)}</span></div>
        <div class="summary-row summary-total"><span>Total</span><span>${formatMoney(order.total_amount)}</span></div>
      </div>
    </div>
  `;
}

function renderOrderError(text) {
  orderDetail.innerHTML = `
    <div class="empty-state">
      <h2>Could not load this order</h2>
      <p class="muted">${escapeHtml(text)}</p>
      <a class="button button-secondary" href="./orders.html">Back to orders</a>
    </div>
  `;
}

async function initOrderDetail() {
  if (!requireAuth()) return;

  const params = new URLSearchParams(window.location.search);
  const id = Number(params.get("id"));

  if (!Number.isInteger(id) || id <= 0) {
    renderOrderError("No valid order id was provided in the URL.");
    return;
  }

  try {
    const order = await api.orders.get(id);
    renderOrderDetail(order);
  } catch (error) {
    renderOrderError(error.message);
  }
}

if (ordersList) {
  initOrdersList();
}

if (orderDetail) {
  initOrderDetail();
}