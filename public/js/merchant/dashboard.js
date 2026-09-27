const API_BASE_URL = "http://localhost:8000";

let agentToggle;
let agentClose;
let agentChat;
let agentMessages;
let agentForm;
let agentInput;
let agentSend;
let agentLoading;
let agentLoadingTimer;

const agentLoadingMessages = [
    "Thinking through your store data",
    "Checking recent activity",
    "Preparing a clear answer",
];

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatInlineMarkdown(value) {
    return value
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/__([^_]+)__/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function isTableSeparator(line) {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function tableCells(line) {
    const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
    return trimmed.split("|").map((cell) => formatInlineMarkdown(escapeHtml(cell.trim())));
}

function renderMarkdown(markdown) {
    const lines = String(markdown ?? "").replace(/\r/g, "").split("\n");
    const output = [];
    let paragraph = [];

    const flushParagraph = () => {
        if (paragraph.length) {
            output.push(`<p>${formatInlineMarkdown(escapeHtml(paragraph.join(" ")))}</p>`);
            paragraph = [];
        }
    };

    for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        const nextLine = lines[index + 1] || "";

        if (line.trim() === "") {
            flushParagraph();
            continue;
        }

        if (line.includes("|") && isTableSeparator(nextLine)) {
            flushParagraph();
            const headers = tableCells(line);
            const rows = [];
            index += 2;
            while (index < lines.length && lines[index].includes("|")) {
                rows.push(tableCells(lines[index]));
                index += 1;
            }
            index -= 1;
            output.push(`
                <div class="merchant-agent-table-wrap"><table>
                    <thead><tr>${headers.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>
                    <tbody>${rows.map((row) => `<tr>${headers.map((_, cellIndex) => `<td>${row[cellIndex] || ""}</td>`).join("")}</tr>`).join("")}</tbody>
                </table></div>
            `);
            continue;
        }

        const heading = line.match(/^(#{1,6})\s+(.+)$/);
        if (heading) {
            flushParagraph();
            const level = heading[1].length;
            output.push(`<h${level}>${formatInlineMarkdown(escapeHtml(heading[2]))}</h${level}>`);
            continue;
        }

        const bullet = line.match(/^\s*[-*]\s+(.+)$/);
        if (bullet) {
            flushParagraph();
            output.push(`<ul><li>${formatInlineMarkdown(escapeHtml(bullet[1]))}</li></ul>`);
            continue;
        }

        const ordered = line.match(/^\s*\d+\.\s+(.+)$/);
        if (ordered) {
            flushParagraph();
            output.push(`<ol><li>${formatInlineMarkdown(escapeHtml(ordered[1]))}</li></ol>`);
            continue;
        }

        paragraph.push(line.trim());
    }

    flushParagraph();
    return output.join("");
}

function addAgentMessage(content, type) {
    const message = document.createElement("div");
    message.className = `merchant-agent-message ${type}-message`;
    if (type === "agent") {
        message.innerHTML = renderMarkdown(content);
    } else {
        message.textContent = content;
    }
    agentMessages.appendChild(message);
    agentMessages.scrollTop = agentMessages.scrollHeight;
}

function setAgentLoading(loading) {
    agentLoading.hidden = !loading;
    agentSend.disabled = loading;
    agentInput.disabled = loading;
    agentChat.classList.toggle("is-loading", loading);
    agentChat.setAttribute("aria-busy", String(loading));

    window.clearInterval(agentLoadingTimer);
    if (!loading) {
        agentLoading.textContent = "";
        return;
    }

    let messageIndex = 0;
    const updateLoadingMessage = () => {
        agentLoading.textContent = agentLoadingMessages[messageIndex];
        messageIndex = (messageIndex + 1) % agentLoadingMessages.length;
    };
    updateLoadingMessage();
    agentLoadingTimer = window.setInterval(updateLoadingMessage, 1800);
}

function setAgentOpen(open) {
    agentChat.hidden = !open;
    agentToggle.setAttribute("aria-expanded", String(open));
    if (open) agentInput.focus();
}

async function sendAgentMessage(event) {
    event.preventDefault();
    const message = agentInput.value.trim();
    const token = localStorage.getItem("access_token");
    if (!message || !token) return;

    addAgentMessage(message, "user");
    agentInput.value = "";
    setAgentLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/merchant/agent/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            let detail = "The agent could not answer right now.";
            try {
                const data = await response.json();
                if (data.detail) detail = Array.isArray(data.detail)
                    ? data.detail.map((item) => item.msg || "Invalid request").join("; ")
                    : data.detail;
            } catch {
                // Keep the friendly fallback for non-JSON errors.
            }
            throw new Error(detail);
        }

        const data = await response.json();
        if (typeof data.response !== "string") {
            throw new Error("The agent returned an unexpected response.");
        }
        addAgentMessage(data.response, "agent");
    } catch (error) {
        console.error("Merchant agent request failed:", error);
        addAgentMessage(error.message || "The agent could not answer right now.", "agent-error");
    } finally {
        setAgentLoading(false);
        agentInput.focus();
    }
}

function initializeAgentChat() {
    agentToggle = document.getElementById("merchant-agent-toggle");
    agentClose = document.getElementById("merchant-agent-close");
    agentChat = document.getElementById("merchant-agent-chat");
    agentMessages = document.getElementById("merchant-agent-messages");
    agentForm = document.getElementById("merchant-agent-form");
    agentInput = document.getElementById("merchant-agent-input");
    agentSend = document.getElementById("merchant-agent-send");
    agentLoading = document.getElementById("merchant-agent-loading");

    if (!agentToggle || !agentClose || !agentChat || !agentMessages || !agentForm || !agentInput || !agentSend || !agentLoading) {
        console.error("Merchant agent chat could not initialize: required chat elements are missing.");
        return;
    }

    agentToggle.addEventListener("click", () => setAgentOpen(agentChat.hidden));
    agentClose.addEventListener("click", () => setAgentOpen(false));
    agentForm.addEventListener("submit", sendAgentMessage);
    agentLoading.setAttribute("role", "status");
    agentInput.addEventListener("input", () => {
        agentInput.style.height = "auto";
        agentInput.style.height = `${Math.min(agentInput.scrollHeight, 120)}px`;
    });
    agentInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (typeof agentForm.requestSubmit === "function") {
                agentForm.requestSubmit();
            } else {
                sendAgentMessage({ preventDefault() {} });
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", initializeAgentChat);


async function loadDashboard() {

    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "../login.html";
        return;
    }

    try {

        const response = await fetch(
            `${API_BASE_URL}/merchant/overview`,
            {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (response.status === 401 || response.status === 403) {
            alert("You are not authorized to access the merchant dashboard.");
            window.location.href = "../login.html";
            return;
        }

        if (!response.ok) {
            throw new Error("Failed to load dashboard");
        }

        const data = await response.json();

        document.getElementById("revenue").textContent =
            `₹${data.revenue.toLocaleString("en-IN")}`;

        document.getElementById("total-orders").textContent =
            data.total_orders;

        document.getElementById("total-products").textContent =
            data.total_products;

        document.getElementById("low-stock").textContent =
            data.low_stock_products;

        document.getElementById("successful-payments").textContent =
            data.successful_payments;

        document.getElementById("failed-payments").textContent =
            data.failed_payments;

    } catch (error) {

        console.error("Dashboard error:", error);

        alert("Unable to load dashboard data.");
    }
}


document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);
