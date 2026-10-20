(() => {
    const serverData = document.getElementById("budgetbuddy-server-data");
    const mainContent = document.querySelector(".main-content");
    const userScope = mainContent ? mainContent.dataset.userId : "guest";
    const storageKey = `budgetBuddyData:${userScope}`;

    // Keep the storage adapter isolated so a server-backed store can replace it later.
    const repository = {
        save(data) {
            localStorage.setItem(storageKey, JSON.stringify(data));
        },
        load() {
            const saved = localStorage.getItem(storageKey);
            return saved ? JSON.parse(saved) : null;
        },
    };

    if (serverData) {
        const data = JSON.parse(serverData.textContent);
        repository.save(data);
    }

    const form = document.getElementById("transaction-form");
    const amountInput = document.getElementById("id_amount");
    const categoryInput = document.getElementById("id_category");
    const typeInput = document.getElementById("id_transaction_type");

    function showError(name, message) {
        const target = document.querySelector(`[data-error-for="${name}"]`);
        if (target) target.textContent = message;
    }

    if (form) {
        form.addEventListener("submit", (event) => {
            let valid = true;
            const amount = Number(amountInput.value);
            if (!Number.isFinite(amount) || amount <= 0) {
                showError("amount", "Please enter a valid amount.");
                valid = false;
            } else {
                showError("amount", "");
            }
            if (!categoryInput.value) {
                showError("category", "Please select a category.");
                valid = false;
            } else {
                showError("category", "");
            }
            if (!typeInput.value) {
                showError("transaction_type", "Please select a transaction type.");
                valid = false;
            } else {
                showError("transaction_type", "");
            }
            if (!valid) event.preventDefault();
        });
    }

    const editButtons = document.querySelectorAll(".edit-transaction");
    const resetButton = document.getElementById("cancel-edit");
    const expenseId = document.getElementById("expense-id");
    const formTitle = document.getElementById("expense-form-title");
    const submitButton = document.getElementById("transaction-submit");

    editButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const transaction = button.closest("[data-transaction]");
            if (!transaction || !form) return;
            expenseId.value = transaction.dataset.id;
            typeInput.value = transaction.dataset.type;
            amountInput.value = transaction.dataset.amount;
            categoryInput.value = transaction.dataset.category;
            document.getElementById("id_description").value = transaction.dataset.description;
            document.getElementById("id_date").value = transaction.dataset.date;
            document.getElementById("id_payment_method").value = transaction.dataset.payment;
            formTitle.textContent = "Edit transaction";
            submitButton.innerHTML = "Update transaction <span>→</span>";
            resetButton.hidden = false;
            form.scrollIntoView({ behavior: "smooth", block: "center" });
        });
    });

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            form.reset();
            expenseId.value = "";
            formTitle.textContent = "Add a transaction";
            submitButton.innerHTML = "Save transaction <span>→</span>";
            resetButton.hidden = true;
        });
    }

    document.querySelectorAll(".delete-transaction-form").forEach((deleteForm) => {
        deleteForm.addEventListener("submit", (event) => {
            if (!window.confirm("Are you sure you want to delete this expense?")) {
                event.preventDefault();
            }
        });
    });

    const transactions = Array.from(document.querySelectorAll("#filtered-transactions [data-transaction]"));
    const search = document.getElementById("transaction-search");
    const category = document.getElementById("filter-category");
    const payment = document.getElementById("filter-payment");
    const type = document.getElementById("filter-type");
    const from = document.getElementById("filter-from");
    const to = document.getElementById("filter-to");
    const sort = document.getElementById("sort-transactions");
    const emptyResults = document.getElementById("no-filter-results");
    let quickRange = "all";

    const calendarGrid = document.getElementById("calendar-grid");
    if (calendarGrid) {
        const calendarLabel = document.getElementById("calendar-month-label");
        const calendarTotal = document.getElementById("calendar-total");
        const calendarToday = new Date(`${mainContent.dataset.today}T00:00:00`);
        let visibleMonth = new Date(calendarToday.getFullYear(), calendarToday.getMonth(), 1);
        let selectedDate = "";
        const weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const monthNames = new Intl.DateTimeFormat("en-PH", { month: "long", year: "numeric" });
        const money = (amount) => `₱${amount.toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        const dailyExpenses = new Map();

        const savedTransactions = serverData
            ? JSON.parse(serverData.textContent).transactions
            : [];
        savedTransactions.forEach((transaction) => {
            if (transaction.type !== "expense") return;
            const amount = Number(transaction.amount);
            if (Number.isFinite(amount)) {
                const day = transaction.date;
                dailyExpenses.set(day, (dailyExpenses.get(day) || 0) + amount);
            }
        });

        function renderCalendar() {
            const year = visibleMonth.getFullYear();
            const month = visibleMonth.getMonth();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const startDay = new Date(year, month, 1).getDay();
            const monthPrefix = `${year}-${String(month + 1).padStart(2, "0")}-`;
            const dayTotals = [];
            let monthlyTotal = 0;
            let maxDaily = 0;

            for (let day = 1; day <= daysInMonth; day += 1) {
                const dateKey = `${monthPrefix}${String(day).padStart(2, "0")}`;
                const amount = dailyExpenses.get(dateKey) || 0;
                dayTotals.push({ day, dateKey, amount });
                monthlyTotal += amount;
                maxDaily = Math.max(maxDaily, amount);
            }

            calendarLabel.textContent = monthNames.format(visibleMonth);
            calendarTotal.textContent = `${money(monthlyTotal)} spent this month`;
            calendarGrid.replaceChildren();
            weekdayNames.forEach((weekday) => {
                const heading = document.createElement("span");
                heading.className = "calendar-weekday";
                heading.setAttribute("role", "columnheader");
                heading.textContent = weekday;
                calendarGrid.appendChild(heading);
            });
            for (let blank = 0; blank < startDay; blank += 1) {
                const emptyCell = document.createElement("span");
                emptyCell.className = "calendar-day empty";
                emptyCell.setAttribute("aria-hidden", "true");
                calendarGrid.appendChild(emptyCell);
            }

            dayTotals.forEach(({ day, dateKey, amount }) => {
                const cell = document.createElement("button");
                cell.type = "button";
                cell.className = "calendar-day";
                cell.setAttribute("role", "gridcell");
                cell.setAttribute(
                    "aria-label",
                    amount
                        ? `${dateKey}: ${money(amount)} spent. View transactions.`
                        : `${dateKey}: no spending. View transactions.`,
                );
                if (amount > 0) {
                    cell.classList.add("has-spending");
                    if (amount / maxDaily >= 0.66) cell.classList.add("spending-high");
                    else if (amount / maxDaily >= 0.33) cell.classList.add("spending-medium");
                }
                if (dateKey === mainContent.dataset.today) cell.classList.add("is-today");
                if (dateKey === selectedDate) cell.classList.add("is-selected");

                const dayLabel = document.createElement("span");
                dayLabel.className = "calendar-day-number";
                dayLabel.textContent = String(day);
                cell.appendChild(dayLabel);
                if (amount > 0) {
                    const amountLabel = document.createElement("span");
                    amountLabel.className = "calendar-day-amount";
                    amountLabel.textContent = money(amount);
                    cell.appendChild(amountLabel);
                }

                cell.addEventListener("click", () => {
                    selectedDate = dateKey;
                    if (!from || !to) {
                        window.location.href = `/transactions/?from=${dateKey}&to=${dateKey}`;
                        return;
                    }
                    from.value = dateKey;
                    to.value = dateKey;
                    quickRange = "all";
                    document.querySelectorAll(".quick-filter").forEach((filter) => {
                        filter.classList.toggle("active", filter.dataset.range === "all");
                    });
                    applyFilters();
                    renderCalendar();
                    document.getElementById("transactions").scrollIntoView({ behavior: "smooth" });
                });
                calendarGrid.appendChild(cell);
            });
        }

        document.getElementById("calendar-previous").addEventListener("click", () => {
            visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
            selectedDate = "";
            renderCalendar();
        });
        document.getElementById("calendar-next").addEventListener("click", () => {
            visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
            selectedDate = "";
            renderCalendar();
        });
        renderCalendar();
    }

    function applyFilters() {
        if (!search || !category || !payment || !type || !from || !to || !sort || !emptyResults) return;
        const todayString = mainContent.dataset.today;
        const today = new Date(`${todayString}T00:00:00`);
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - ((today.getDay() + 6) % 7));
        const startOfMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-01`;
        const query = search.value.trim().toLocaleLowerCase();
        let shown = transactions.filter((item) => {
            const text = `${item.dataset.category} ${item.dataset.description} ${item.dataset.payment}`.toLocaleLowerCase();
            const itemDate = item.dataset.date;
            const matchesQuick = quickRange === "all"
                || (quickRange === "today" && itemDate === todayString)
                || (quickRange === "week" && itemDate >= startOfWeek.toISOString().slice(0, 10))
                || (quickRange === "month" && itemDate >= startOfMonth && itemDate <= todayString);
            return (!query || text.includes(query))
                && (!category.value || item.dataset.category === category.value)
                && (!payment.value || item.dataset.payment === payment.value)
                && (!type.value || item.dataset.type === type.value)
                && (!from.value || itemDate >= from.value)
                && (!to.value || itemDate <= to.value)
                && matchesQuick;
        });

        shown.sort((first, second) => {
            if (sort.value === "oldest") return first.dataset.date.localeCompare(second.dataset.date);
            if (sort.value === "highest") return Number(second.dataset.amount) - Number(first.dataset.amount);
            if (sort.value === "lowest") return Number(first.dataset.amount) - Number(second.dataset.amount);
            return second.dataset.date.localeCompare(first.dataset.date);
        });
        shown.forEach((item) => item.parentElement.appendChild(item));
        transactions.forEach((item) => { item.hidden = !shown.includes(item); });
        emptyResults.hidden = shown.length !== 0 || transactions.length === 0;
    }

    if (search && category && payment && type && from && to && sort && emptyResults) {
        [search, category, payment, type, from, to, sort].forEach((control) => {
            control.addEventListener("input", applyFilters);
            control.addEventListener("change", applyFilters);
        });
        document.querySelectorAll(".quick-filter").forEach((button) => {
            button.addEventListener("click", () => {
                quickRange = button.dataset.range;
                document.querySelectorAll(".quick-filter").forEach((filter) => filter.classList.remove("active"));
                button.classList.add("active");
                applyFilters();
            });
        });
    }
    applyFilters();
})();
