
let revenueChart;
let fleetChart;

function formatCurrency(value) {
    return "₹" + Number(value).toLocaleString("en-IN");
}


// -------------------------
// Business dashboard
// -------------------------

async function loadDashboard() {

    const response = await fetch("/api/dashboard");

    if (!response.ok) {
        throw new Error("Unable to load dashboard data");
    }

    const data = await response.json();
    const m = data.metrics;

    document.getElementById("rental-value").textContent =
        formatCurrency(m.total_rental_value);

    document.getElementById("collected").textContent =
        formatCurrency(m.total_collected);

    document.getElementById("outstanding").textContent =
        formatCurrency(m.outstanding);

    document.getElementById("utilization").textContent =
        m.utilization + "%";

    document.getElementById("active-rentals").textContent =
        m.active_rentals;

    document.getElementById("pending-quotes").textContent =
        m.pending_quotations;

    document.getElementById("overdue").textContent =
        m.overdue_invoices;

    document.getElementById("equipment-count").textContent =
        m.total_equipment;

    document.getElementById("alert-outstanding").textContent =
        formatCurrency(m.outstanding);

    document.getElementById("alert-overdue").textContent =
        m.overdue_invoices + " invoices";

    document.getElementById("alert-quotes").textContent =
        m.pending_quotations + " quotations";

    renderRevenueChart(data.monthly);
    renderFleetChart(data.categories);
    renderTopEquipment(data.top_equipment);
}


function renderRevenueChart(data) {

    const ctx = document.getElementById("revenueChart");

    if (revenueChart) revenueChart.destroy();

    revenueChart = new Chart(ctx, {
        type: "bar",

        data: {
            labels: data.map(item => item.month),

            datasets: [{
                label: "Rental contract value",
                data: data.map(item => item.amount),
                backgroundColor: "#4b91e8",
                borderRadius: 6
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: true,

            plugins: {
                legend: { display: false }
            },

            scales: {
                y: {
                    ticks: {
                        color: "#94a6c2",
                        callback: value =>
                            "₹" + (value / 100000).toFixed(0) + "L"
                    },
                    grid: { color: "#28364e" }
                },

                x: {
                    ticks: { color: "#94a6c2" },
                    grid: { display: false }
                }
            }
        }
    });
}


function renderFleetChart(data) {

    const ctx = document.getElementById("fleetChart");

    if (fleetChart) fleetChart.destroy();

    fleetChart = new Chart(ctx, {
        type: "doughnut",

        data: {
            labels: data.map(item => item.category),

            datasets: [{
                data: data.map(item => item.total),

                backgroundColor: [
                    "#4b91e8",
                    "#45c5a1",
                    "#f2b75a",
                    "#a98bdf",
                    "#e47b91",
                    "#63b5d1"
                ],

                borderWidth: 0
            }]
        },

        options: {
            responsive: true,

            plugins: {
                legend: {
                    position: "bottom",

                    labels: {
                        color: "#b6c4d9",
                        padding: 12,
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}


function renderTopEquipment(data) {

    const container = document.getElementById("equipment-list");

    container.replaceChildren();

    data.forEach(item => {

        const row = document.createElement("div");
        row.className = "equipment-row";

        const name = document.createElement("span");
        name.textContent = item.name;

        const value = document.createElement("strong");
        value.textContent = formatCurrency(item.value);

        row.appendChild(name);
        row.appendChild(value);

        container.appendChild(row);
    });
}


// -------------------------
// Gmail integration
// -------------------------

async function refreshGmailStatus() {

    const status = document.getElementById("gmail-status");
    const connected = document.getElementById("gmail-connected");
    const disconnected = document.getElementById("gmail-disconnected");
    const error = document.getElementById("gmail-error");
    const message = document.getElementById("gmail-message");
    const refreshButton = document.getElementById("gmail-refresh");

    status.textContent = "Checking...";
    status.className = "gmail-status";

    connected.hidden = true;
    disconnected.hidden = true;
    error.hidden = true;
    message.textContent = "";

    if (refreshButton) {
        refreshButton.disabled = true;
        refreshButton.textContent = "Checking...";
    }

    try {

        const statusResponse = await fetch("/api/gmail/status");

        if (!statusResponse.ok) {
            throw new Error("Could not check Gmail connection.");
        }

        const statusData = await statusResponse.json();

        if (!statusData.connected) {

            status.textContent = "Not connected";
            status.className = "gmail-status disconnected";

            disconnected.hidden = false;

            return;
        }

        const profileResponse = await fetch("/api/gmail/profile");

        if (!profileResponse.ok) {
            throw new Error("Could not retrieve Gmail profile.");
        }

        const profileData = await profileResponse.json();

        if (!profileData.connected || !profileData.account) {
            throw new Error("Gmail profile is unavailable.");
        }

        const account = profileData.account;

        document.getElementById("gmail-account").textContent =
            account.email || "Connected Gmail account";

        document.getElementById("gmail-messages").textContent =
            Number(account.total_messages || 0).toLocaleString("en-IN");

        document.getElementById("gmail-threads").textContent =
            Number(account.total_threads || 0).toLocaleString("en-IN");

        status.textContent = "● Connected";
        status.className = "gmail-status connected";

        connected.hidden = false;

    } catch (err) {

        console.error("Gmail status error:", err);

        status.textContent = "Status unavailable";
        status.className = "gmail-status error";

        error.hidden = false;

        message.textContent =
            err.message || "Unable to check Gmail connection.";

    } finally {

        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = "↻ Refresh status";
        }
    }
}


// -------------------------
// Business query assistant
// -------------------------

async function askQuestion(question) {

    const input = document.getElementById("question");
    const answer = document.getElementById("answer");
    const sources = document.getElementById("sources");
    const askButton = document.getElementById("ask-button");

    const query = question || input.value.trim();

    if (!query) return;

    answer.textContent = "Analyzing your business data...";
    sources.replaceChildren();

    askButton.disabled = true;
    askButton.textContent = "Thinking...";

    try {

        const response = await fetch("/api/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: query
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Request failed");
        }

        answer.textContent =
            result.answer || "No answer available.";

        if (result.sources && result.sources.length > 0) {

            const heading = document.createElement("h4");

            heading.textContent =
                `Sources (${result.sources.length})`;

            sources.appendChild(heading);

            result.sources.forEach(source => {

                const item = document.createElement("div");
                item.className = "source-item";

                const record = document.createElement("strong");
                record.textContent = source.record_id;

                const detail = document.createElement("span");

                detail.textContent =
                    `${source.table} · ${source.detail}`;

                item.appendChild(record);
                item.appendChild(detail);

                sources.appendChild(item);
            });

        } else {

            sources.textContent =
                "No supporting records available.";
        }

    } catch (error) {

        answer.textContent =
            error.message || "Unable to process the question.";

    } finally {

        askButton.disabled = false;
        askButton.textContent = "Ask →";
    }
}


// -------------------------
// Initialize dashboard
// -------------------------

document.addEventListener("DOMContentLoaded", () => {

    loadDashboard().catch(error => {

        console.error("Dashboard error:", error);

        document.getElementById("rental-value").textContent =
            "Load failed";
    });

    refreshGmailStatus();

    document.getElementById("question").addEventListener(
        "keydown",
        event => {
            if (event.key === "Enter") {
                askQuestion();
            }
        }
    );
});
