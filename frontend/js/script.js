// Use Flask directly unless we're already served by Flask (port 5000).
// This covers: file:// open, VS Code Live Server (port 5500), and any other dev server.
const API = "http://localhost:5000/api";

const urlInput = document.getElementById("urlInput");
const shortenBtn = document.getElementById("shortenBtn");
const result = document.getElementById("result");
const shortUrl = document.getElementById("shortUrl");
const message = document.getElementById("message");
const historyBody = document.getElementById("historyBody");
const searchInput = document.getElementById("searchInput");

let currentShortUrl = "";

function showMessage(text, error = false) {
    message.textContent = text;
    message.style.color = error ? "#d32f2f" : "#15934a";
}

function isHttpUrl(value) {
    try {
        const parsed = new URL(value);
        return parsed.protocol === "http:" || parsed.protocol === "https:";
    } catch {
        return false;
    }
}

function displayShortUrl(url) {
    currentShortUrl = url;
    shortUrl.href = url;
    shortUrl.textContent = url;
    result.classList.remove("hidden");
}

function restoreLastShortUrl() {
    const saved = localStorage.getItem("lastShortUrl");
    if (isHttpUrl(saved)) {
        displayShortUrl(saved);
    }
}

async function shortenUrl() {
    const url = urlInput.value.trim();

    if (!url) {
        showMessage("Please enter a URL.", true);
        return;
    }

    try {
        const response = await fetch(`${API}/shorten`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        const resultData = await response.json();

        if (!response.ok) {
            throw new Error(resultData.error || "Could not shorten URL.");
        }

        const createdShortUrl = resultData.data.short_url;
        localStorage.setItem("lastShortUrl", createdShortUrl);
        displayShortUrl(createdShortUrl);
        showMessage("URL shortened successfully.");
        urlInput.value = "";

        await loadHistory();
        await loadStats();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function loadHistory() {
    const search = encodeURIComponent(searchInput.value.trim());

    try {
        const response = await fetch(`${API}/history?search=${search}`);
        const resultData = await response.json();

        historyBody.innerHTML = "";

        resultData.data.forEach((item, index) => {
            const row = document.createElement("tr");
            const safeShortUrl = encodeURI(item.short_url);

            row.innerHTML = `
                <td>${index + 1}</td>
                <td title="${escapeHtml(item.original_url)}">
                    ${truncate(item.original_url, 45)}
                </td>
                <td>
                    <a href="${safeShortUrl}" target="_blank" rel="noopener noreferrer">
                        ${escapeHtml(item.short_code)}
                    </a>
                    <button type="button" data-copy="${escapeHtml(item.short_url)}">📋</button>
                </td>
                <td>${formatDate(item.created_at)}</td>
                <td>${item.click_count}</td>
                <td>
                    <div class="actions">
                        <button type="button" data-open="${escapeHtml(item.short_url)}">Open</button>
                        <button type="button" class="edit" data-edit="${item.id}">Edit</button>
                        <button type="button" class="delete" data-delete="${item.id}">Delete</button>
                    </div>
                </td>
            `;

            historyBody.appendChild(row);
        });

        if (resultData.data.length === 0) {
            historyBody.innerHTML =
                `<tr><td colspan="6">No shortened URLs found.</td></tr>`;
        }
    } catch (error) {
        showMessage("Could not load history. Is Flask running?", true);
    }
}

async function editUrl(id) {
    try {
        const response = await fetch(`${API}/urls/${id}`);
        const resultData = await response.json();

        if (!response.ok) throw new Error(resultData.error);

        const newUrl = prompt(
            "Edit original URL:",
            resultData.data.original_url
        );

        if (!newUrl || newUrl === resultData.data.original_url) return;

        const updateResponse = await fetch(`${API}/urls/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: newUrl.trim() })
        });

        const updated = await updateResponse.json();

        if (!updateResponse.ok) throw new Error(updated.error);

        showMessage("URL updated successfully.");
        await loadHistory();
        await loadStats();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteUrl(id) {
    if (!confirm("Delete this shortened URL?")) return;

    try {
        const response = await fetch(`${API}/urls/${id}`, {
            method: "DELETE"
        });

        const resultData = await response.json();

        if (!response.ok) throw new Error(resultData.error);

        showMessage("URL deleted successfully.");
        await loadHistory();
        await loadStats();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function clearHistory() {
    if (!confirm("Delete ALL URL history? This cannot be undone.")) return;

    try {
        const response = await fetch(`${API}/history`, {
            method: "DELETE"
        });

        if (!response.ok) throw new Error("Could not clear history.");

        result.classList.add("hidden");
        currentShortUrl = "";
        shortUrl.removeAttribute("href");
        shortUrl.textContent = "";
        localStorage.removeItem("lastShortUrl");
        showMessage("History cleared.");
        await loadHistory();
        await loadStats();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API}/stats`);
        const resultData = await response.json();

        document.getElementById("totalUrls").textContent =
            resultData.data.total_urls;

        document.getElementById("totalClicks").textContent =
            resultData.data.total_clicks;

        const historyResponse = await fetch(`${API}/history`);
        const historyData = await historyResponse.json();

        const today = new Date().toISOString().slice(0, 10);
        const createdToday = historyData.data.filter(item =>
            item.created_at.startsWith(today)
        ).length;

        document.getElementById("createdToday").textContent = createdToday;
        document.getElementById("activeLinks").textContent =
            resultData.data.total_urls;
    } catch (error) {
        console.error(error);
    }
}

function copyText(text) {
    if (!isHttpUrl(text)) {
        showMessage("No short URL available to copy.", true);
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => showMessage("Copied to clipboard."))
        .catch(() => showMessage("Could not copy URL.", true));
}

function openUrl(url) {
    const finalUrl = isHttpUrl(url) ? url : currentShortUrl;

    if (!isHttpUrl(finalUrl)) {
        showMessage("No short URL available. Shorten a URL first.", true);
        return;
    }

    const opened = window.open(finalUrl, "_blank", "noopener,noreferrer");
    if (!opened) {
        window.location.href = finalUrl;
    }
}

async function shareUrl() {
    if (!isHttpUrl(currentShortUrl)) {
        showMessage("Create a short URL first.", true);
        return;
    }

    if (navigator.share) {
        await navigator.share({
            title: "Short URL",
            url: currentShortUrl
        });
    } else {
        copyText(currentShortUrl);
    }
}

function formatDate(value) {
    return new Date(value).toLocaleString();
}

function truncate(value, length) {
    return value.length > length
        ? value.substring(0, length) + "..."
        : value;
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    }[char]));
}

shortenBtn.addEventListener("click", shortenUrl);
document.getElementById("copyBtn").addEventListener("click", () => copyText(currentShortUrl));
document.getElementById("openBtn").addEventListener("click", () => openUrl(currentShortUrl));
document.getElementById("shareBtn").addEventListener("click", shareUrl);
document.getElementById("quickCopy").addEventListener("click", () => copyText(currentShortUrl));
document.getElementById("quickOpen").addEventListener("click", () => openUrl(currentShortUrl));
document.getElementById("quickShare").addEventListener("click", shareUrl);
document.getElementById("refreshBtn").addEventListener("click", () => {
    loadHistory();
    loadStats();
});
document.getElementById("historyRefresh").addEventListener("click", loadHistory);
document.getElementById("clearBtn").addEventListener("click", clearHistory);

historyBody.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    if (target.dataset.copy) {
        copyText(target.dataset.copy);
    } else if (target.dataset.open) {
        openUrl(target.dataset.open);
    } else if (target.dataset.edit) {
        editUrl(Number(target.dataset.edit));
    } else if (target.dataset.delete) {
        deleteUrl(Number(target.dataset.delete));
    }
});

let searchTimer;
searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadHistory, 300);
});

restoreLastShortUrl();
loadHistory();
loadStats();
