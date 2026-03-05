/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillStart, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { loadBundle } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";

class OpenAIBillingDashboard extends Component {
    static template = "openai_billing.Dashboard";

    setup() {
        this.state = useState({
            kpis: {},
            charts: {},
            date_filter: "this_month",
            loading: true,
        });

        this.costByDeptRef = useRef("costByDeptChart");
        this.usageByModelRef = useRef("usageByModelChart");
        this.costByPurposeRef = useRef("costByPurposeChart");
        this.quotaUtilRef = useRef("quotaUtilChart");

        this._chartInstances = {};
        this._needsChartRender = false;

        // Load Chart.js bundle and fetch data BEFORE the component mounts
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this._fetchData();
        });

        // Render charts AFTER the DOM is ready
        onMounted(() => this._renderCharts());

        // Re-render charts after OWL patches the DOM (e.g. filter change)
        onPatched(() => {
            if (this._needsChartRender && !this.state.loading) {
                this._needsChartRender = false;
                this._renderCharts();
            }
        });
    }

    /* ------------------------------------------------------------------ */
    /*  Data loading                                                       */
    /* ------------------------------------------------------------------ */
    async _fetchData() {
        try {
            const [kpis, charts] = await Promise.all([
                rpc("/openai_billing/dashboard/kpis", {
                    date_filter: this.state.date_filter,
                }),
                rpc("/openai_billing/dashboard/charts", {
                    date_filter: this.state.date_filter,
                }),
            ]);
            this.state.kpis = kpis;
            this.state.charts = charts;
        } catch (err) {
            console.error("OpenAI Billing Dashboard error:", err);
        }
        this.state.loading = false;
    }

    async onFilterChange(ev) {
        this.state.date_filter = ev.target.value;
        this.state.loading = true;
        this._needsChartRender = true;
        await this._fetchData();
        // onPatched will call _renderCharts once OWL has finished
        // patching the DOM and the canvas refs are available.
    }

    /* ------------------------------------------------------------------ */
    /*  Formatting helpers                                                 */
    /* ------------------------------------------------------------------ */
    formatNumber(num) {
        if (!num) return "0";
        if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
        if (num >= 1_000) return (num / 1_000).toFixed(1) + "K";
        return Number(num).toLocaleString();
    }

    formatCurrency(num) {
        if (!num) return "$0.00";
        return (
            "$" +
            Number(num).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            })
        );
    }

    formatEnergy(kwh) {
        if (!kwh) return "0 Wh";
        if (kwh >= 1000) return (kwh / 1000).toFixed(1) + " MWh";
        if (kwh >= 1) return kwh.toFixed(2) + " kWh";
        return (kwh * 1000).toFixed(1) + " Wh";
    }

    formatCO2(grams) {
        if (!grams) return "0 g";
        if (grams >= 1000000) return (grams / 1000000).toFixed(1) + " t";
        if (grams >= 1000) return (grams / 1000).toFixed(1) + " kg";
        return grams.toFixed(1) + " g";
    }

    /* ------------------------------------------------------------------ */
    /*  Chart rendering (Chart.js)                                         */
    /* ------------------------------------------------------------------ */
    _destroyCharts() {
        Object.values(this._chartInstances).forEach((c) => c?.destroy());
        this._chartInstances = {};
    }

    _renderCharts() {
        this._destroyCharts();
        const data = this.state.charts;
        if (!data) return;

        /* ---------- OpenAI-brand palette ---------- */
        const palette = [
            "#10a37f", "#1a7f64", "#06b6d4", "#0ea5e9",
            "#8b5cf6", "#a78bfa", "#f59e0b", "#f97316",
            "#ef4444", "#6b7280",
        ];

        /* ---------- Chart.js global dark-theme defaults ---------- */
        const txtColor = "#acacac";
        const gridColor = "rgba(255,255,255,0.06)";
        Chart.defaults.color = txtColor;
        Chart.defaults.borderColor = gridColor;
        Chart.defaults.plugins.title.color = "#ececec";
        Chart.defaults.plugins.legend.labels.color = txtColor;

        // 1 — Cost by Department (vertical bar)
        this._bar(
            this.costByDeptRef,
            "costByDept",
            data.cost_by_department,
            "Cost by Department (USD)",
            palette,
            { yPrefix: "$", xAxisTitle: "Department", yAxisTitle: "Cost (USD)" }
        );

        // 2 — Token Usage by Model (horizontal bar)
        this._bar(
            this.usageByModelRef,
            "usageByModel",
            data.usage_by_model,
            "Token Usage by Model",
            palette,
            { horizontal: true, xAxisTitle: "Tokens", yAxisTitle: "Model" }
        );

        // 3 — Cost by Purpose (pie)
        if (this.costByPurposeRef.el && data.cost_by_purpose) {
            const ctx = this.costByPurposeRef.el.getContext("2d");
            this._chartInstances.costByPurpose = new Chart(ctx, {
                type: "pie",
                data: {
                    labels: data.cost_by_purpose.labels,
                    datasets: [
                        {
                            data: data.cost_by_purpose.data,
                            backgroundColor: palette.slice(
                                0,
                                data.cost_by_purpose.labels.length
                            ),
                            borderColor: "#171717",
                            borderWidth: 2,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.6,
                    plugins: {
                        title: {
                            display: true,
                            text: "Cost by Purpose",
                            font: { size: 13, weight: "600" },
                            color: "#ececec",
                        },
                        legend: {
                            position: "bottom",
                            labels: {
                                font: { size: 10 },
                                padding: 12,
                                color: "#acacac",
                            },
                        },
                    },
                },
            });
        }

        // 4 — Quota Utilisation (horizontal bar with colour coding)
        if (this.quotaUtilRef.el && data.department_quotas) {
            const ctx = this.quotaUtilRef.el.getContext("2d");
            const q = data.department_quotas;
            const barColors = q.map((d) =>
                d.percentage >= 100
                    ? "#ef4444"
                    : d.percentage >= 80
                    ? "#f59e0b"
                    : "#10a37f"
            );
            this._chartInstances.quotaUtil = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: q.map((d) => d.name),
                    datasets: [
                        {
                            label: "Usage %",
                            data: q.map((d) => d.percentage),
                            backgroundColor: barColors,
                            borderRadius: 4,
                        },
                    ],
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: "Department Quota Utilisation",
                            font: { size: 13, weight: "600" },
                            color: "#ececec",
                        },
                        legend: { display: false },
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 120,
                            grid: { color: gridColor },
                            title: { display: true, text: "Utilisation %", font: { size: 11 }, color: txtColor },
                            ticks: {
                                callback: (v) => v + "%",
                                font: { size: 9 },
                                color: txtColor,
                            },
                        },
                        y: {
                            grid: { color: gridColor },
                            title: { display: true, text: "Department", font: { size: 11 }, color: txtColor },
                            ticks: { font: { size: 9 }, color: txtColor },
                        },
                    },
                },
            });
        }
    }

    /**
     * Helper: create a bar chart (vertical or horizontal).
     */
    _bar(ref, key, dataset, title, palette, opts = {}) {
        if (!ref.el || !dataset) return;
        const ctx = ref.el.getContext("2d");
        const txtColor = "#acacac";
        const gridColor = "rgba(255,255,255,0.06)";
        const yTickCb = opts.yPrefix
            ? (v) => opts.yPrefix + v.toFixed(2)
            : undefined;
        this._chartInstances[key] = new Chart(ctx, {
            type: "bar",
            data: {
                labels: dataset.labels,
                datasets: [
                    {
                        label: title,
                        data: dataset.data,
                        backgroundColor: palette.slice(
                            0,
                            dataset.labels.length
                        ),
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                indexAxis: opts.horizontal ? "y" : "x",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: title,
                        font: { size: 13, weight: "600" },
                        color: "#ececec",
                    },
                    legend: { display: false },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: gridColor },
                        title: {
                            display: true,
                            text: opts.horizontal ? (opts.yAxisTitle || "") : (opts.xAxisTitle || ""),
                            font: { size: 11 },
                            color: txtColor,
                        },
                        ticks: {
                            callback: opts.horizontal ? yTickCb : undefined,
                            font: { size: 9 },
                            color: txtColor,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: gridColor },
                        title: {
                            display: true,
                            text: opts.horizontal ? (opts.xAxisTitle || "") : (opts.yAxisTitle || ""),
                            font: { size: 11 },
                            color: txtColor,
                        },
                        ticks: {
                            callback: opts.horizontal ? undefined : yTickCb,
                            font: { size: 9 },
                            color: txtColor,
                        },
                    },
                },
            },
        });
    }
}

registry
    .category("actions")
    .add("openai_billing_dashboard", OpenAIBillingDashboard);
