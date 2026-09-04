const loginForm = document.querySelector("#loginForm");
const chatPanel = document.querySelector("#chatPanel");
const loginError = document.querySelector("#loginError");
const chatError = document.querySelector("#chatError");
const messages = document.querySelector("#messages");
const input = document.querySelector("#messageInput");
const statusText = document.querySelector("#connectionStatus");

function showError(node, message) { node.textContent = message; node.hidden = false; }
function clearError(node) { node.hidden = true; node.textContent = ""; }

function appendInline(parent, text) {
  const pattern = /(\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|\*\*(.+?)\*\*|`([^`]+)`|(https?:\/\/[^\s]+))/g;
  let cursor = 0;
  let match;
  while ((match = pattern.exec(text))) {
    if (match.index > cursor) parent.appendChild(document.createTextNode(text.slice(cursor, match.index)));
    if (match[2] && match[3]) {
      const link = document.createElement("a");
      link.href = match[3]; link.target = "_blank"; link.rel = "noopener noreferrer";
      link.textContent = match[2]; parent.appendChild(link);
    } else if (match[4]) {
      const strong = document.createElement("strong"); strong.textContent = match[4]; parent.appendChild(strong);
    } else if (match[5]) {
      const code = document.createElement("code"); code.textContent = match[5]; parent.appendChild(code);
    } else {
      const link = document.createElement("a");
      link.href = match[6].replace(/[).,]+$/, ""); link.target = "_blank"; link.rel = "noopener noreferrer";
      link.textContent = match[6]; parent.appendChild(link);
    }
    cursor = pattern.lastIndex;
  }
  if (cursor < text.length) parent.appendChild(document.createTextNode(text.slice(cursor)));
}

function tableCells(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
}

function renderMarkdown(container, markdown) {
  const lines = String(markdown || "").replace(/\r/g, "").split("\n");
  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }

    if (index + 1 < lines.length && line.includes("|") && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[index + 1])) {
      const table = document.createElement("table");
      const head = document.createElement("thead");
      const headerRow = document.createElement("tr");
      tableCells(line).forEach((cell) => { const th = document.createElement("th"); appendInline(th, cell); headerRow.appendChild(th); });
      head.appendChild(headerRow); table.appendChild(head);
      const body = document.createElement("tbody"); index += 2;
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        const row = document.createElement("tr"); tableCells(lines[index]).forEach((cell) => { const td = document.createElement("td"); appendInline(td, cell); row.appendChild(td); });
        body.appendChild(row); index += 1;
      }
      table.appendChild(body); container.appendChild(table); continue;
    }

    const listMatch = line.match(/^\s*[-*]\s+(.+)/);
    if (listMatch) {
      const list = document.createElement("ul");
      while (index < lines.length) {
        const item = lines[index].match(/^\s*[-*]\s+(.+)/); if (!item) break;
        const li = document.createElement("li"); appendInline(li, item[1]); list.appendChild(li); index += 1;
      }
      container.appendChild(list); continue;
    }

    const headingMatch = line.match(/^#{1,3}\s+(.+)/);
    if (headingMatch) { const heading = document.createElement("h3"); appendInline(heading, headingMatch[1]); container.appendChild(heading); index += 1; continue; }

    const paragraph = document.createElement("p");
    while (index < lines.length && lines[index].trim() && !/^\s*[-*]\s+/.test(lines[index]) && !/^#{1,3}\s+/.test(lines[index])) {
      if (index + 1 < lines.length && lines[index].includes("|") && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[index + 1])) break;
      if (paragraph.childNodes.length) paragraph.appendChild(document.createElement("br"));
      appendInline(paragraph, lines[index]); index += 1;
    }
    container.appendChild(paragraph);
  }
}

function addMessage(text, role) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  if (role.includes("assistant")) renderMarkdown(bubble, text);
  else bubble.textContent = text;
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault(); clearError(loginError);
  const button = loginForm.querySelector("button"); button.disabled = true; button.textContent = "Connecting…";
  try {
    const body = Object.fromEntries(new FormData(loginForm));
    const response = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Login failed");
    loginForm.hidden = true; chatPanel.hidden = false; statusText.textContent = `Connected as ${data.email}`; input.focus();
  } catch (error) { showError(loginError, error.message); }
  finally { button.disabled = false; button.textContent = "Connect to store ↗"; }
});

document.querySelector("#chatForm").addEventListener("submit", async (event) => {
  event.preventDefault(); clearError(chatError); const text = input.value.trim(); if (!text) return;
  addMessage(text, "user"); input.value = ""; input.disabled = true;
  const pending = addMessage("Discovering tools and thinking…", "assistant pending");
  try {
    const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text }) });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Agent request failed");
    pending.remove(); addMessage(data.response, "assistant"); statusText.textContent = `${data.tools.length} merchant tools discovered`;
  } catch (error) { pending.remove(); showError(chatError, error.message); }
  finally { input.disabled = false; input.focus(); }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    document.querySelector("#chatForm").requestSubmit();
  }
});
document.querySelector("#logoutButton").addEventListener("click", async () => { await fetch("/api/logout", { method: "POST" }); location.reload(); });
