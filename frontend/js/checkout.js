import { api } from "./api.js";
import { requireAuth } from "./auth.js";

const RAZORPAY_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";

let razorpayScriptPromise = null;

// Load Razorpay's official checkout script only when a payment is actually
// being created (not on every page load).
function loadRazorpayScript() {
  if (window.Razorpay) return Promise.resolve(window.Razorpay);
  if (razorpayScriptPromise) return razorpayScriptPromise;

  razorpayScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = RAZORPAY_SCRIPT_URL;
    script.async = true;
    script.onload = () => resolve(window.Razorpay);
    script.onerror = () => {
      razorpayScriptPromise = null;
      reject(new Error("Could not load the payment gateway. Please try again."));
    };
    document.head.appendChild(script);
  });

  return razorpayScriptPromise;
}

// Runs the full checkout sequence:
//   POST /orders/checkout
//     -> POST /payments/create/{order_id}
//       -> Razorpay Checkout modal
//         -> POST /payments/verify
// The backend does the actual signature verification.
// Resolves with the created order id; throws (Error) on any failure.
export async function runCheckout() {
  if (!requireAuth()) return null;

  const order = await api.orders.checkout();
  const payment = await api.payments.create(order.id);

  await loadRazorpayScript();

  const amountInPaise = Math.round(Number(payment.amount) * 100);
  if (!Number.isFinite(amountInPaise) || amountInPaise <= 0) {
    throw new Error("Invalid payment amount returned by the server.");
  }

  await new Promise((resolve, reject) => {
    const razorpay = new window.Razorpay({
      key: payment.razorpay_key_id,
      amount: amountInPaise,
      currency: payment.currency || "INR",
      name: "ShopAI",
      description: `Order ${order.order_number}`,
      order_id: payment.razorpay_order_id,
      handler: async (response) => {
        try {
          await api.payments.verify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          resolve();
        } catch (error) {
          await api.payments.fail(order.id).catch(() => {});
          reject(new Error(`Payment verification failed: ${error.message}`));
        }
      },
      theme: { color: "#17181a" },
    });

    razorpay.on("payment.failed", (response) => {
      api.payments.fail(order.id).catch(() => {});
      const description =
        response?.error?.description || "Payment was not completed. Please try again.";
      reject(new Error(description));
    });

    razorpay.on("modal.ondismiss", () => {
      api.payments.fail(order.id).catch(() => {});
      reject(new Error("Payment was cancelled."));
    });

    razorpay.open();
  });

  return order.id;
}
