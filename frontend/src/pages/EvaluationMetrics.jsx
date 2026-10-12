import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { getEvaluationMetrics } from "../api/lexintel";
import "./EvaluationMetrics.css";

const pipelineStages = [
    "User Query",
    "Embedding Generation",
    "Hybrid Retrieval",
    "PostgreSQL + pgvector",
    "Configured LLM",
    "Citation-based Response",
];

const metricDescriptions = {
    "Documents Uploaded": "All legal documents currently stored in PostgreSQL.",
    "Documents Processed": "Documents with one or more persisted text chunks.",
    "Total Chunks": "Persisted document chunks available to retrieval.",
    "Questions Asked": "Valid questions received by this API process since its last start.",
    "Average Response Time": "Mean end-to-end RAG pipeline time for this API process.",
    "Retrieval Time": "Mean measured retrieval stage time for this API process.",
    "Retrieval Successes": "Questions that returned at least one citation.",
    "Retrieval Success Rate": "Questions with citations divided by all recorded questions.",
    "Average Citation Relevance": "Mean relevance score of citations returned by this process.",
    "API Status": "Whether this metrics endpoint responded successfully.",
    "Database Status": "Whether the API can connect to and query PostgreSQL.",
};

function formatCount(value) {
    return Number.isInteger(value) ? value.toLocaleString() : "Unavailable";
}

function formatSeconds(value) {
    return Number.isFinite(value) ? `${value.toFixed(2)} sec` : "Not measured";
}

function percent(value, total) {
    return total > 0 ? `${((value / total) * 100).toFixed(1)}%` : "Not measured";
}

function MetricCard({ label, value, loading }) {
    const description = metricDescriptions[label];

    return (
        <article className="em-metric-card">
            <div className="em-metric-card-heading">
                <h3>{label}</h3>
                <details className="em-tooltip">
                    <summary aria-label={`About ${label}`}>i</summary>
                    <p role="tooltip">{description}</p>
                </details>
            </div>
            {loading ? (
                <span
                    className="em-skeleton"
                    aria-label={`Loading ${label}`}
                    role="status"
                />
            ) : (
                <p className="em-metric-value">{value}</p>
            )}
            <p className="em-metric-detail">{description}</p>
        </article>
    );
}

function ChartPanel({ title, summary, children }) {
    const summaryId = `chart-summary-${title.toLowerCase().replaceAll(" ", "-")}`;

    return (
        <section className="em-panel em-chart-panel" aria-labelledby={summaryId}>
            <h3 id={summaryId}>{title}</h3>
            <figure aria-labelledby={summaryId} aria-describedby={`${summaryId}-description`}>
                {children}
                <figcaption id={`${summaryId}-description`}>{summary}</figcaption>
            </figure>
        </section>
    );
}

function MetricTable({ caption, rows, headers }) {
    return (
        <div className="em-table-scroll" tabIndex="0" aria-label={`${caption} table`}>
            <table className="em-table">
                <caption>{caption}</caption>
                <thead>
                    <tr>
                        {headers.map((header) => (
                            <th scope="col" key={header.key}>
                                {header.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.length > 0 ? (
                        rows.map((row) => (
                            <tr key={row[headers[0].key]}>
                                {headers.map((header) =>
                                    header.key === headers[0].key ? (
                                        <th scope="row" key={header.key}>
                                            {row[header.key]}
                                        </th>
                                    ) : (
                                        <td key={header.key}>
                                            {header.key === "status" ? (
                                                <span
                                                    className={`em-status em-status-${row.status.toLowerCase().replaceAll(" ", "-")}`}
                                                >
                                                    {row.status}
                                                </span>
                                            ) : (
                                                row[header.key]
                                            )}
                                        </td>
                                    )
                                )}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td className="em-table-empty" colSpan={headers.length}>
                                The service records aggregate query totals only.
                                Question text is not retained.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

function usePageFocus() {
    const headingRef = useRef(null);

    useEffect(() => {
        headingRef.current?.focus();
    }, []);

    return headingRef;
}

function EvaluationMetrics() {
    const headingRef = usePageFocus();
    const [metrics, setMetrics] = useState(null);
    const [charts, setCharts] = useState({
        responseTimes: [],
        retrievalOutcomes: [],
    });
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");
    const [refreshCount, setRefreshCount] = useState(0);

    useEffect(() => {
        let isCurrent = true;

        async function refresh() {
            setIsLoading(true);
            setErrorMessage("");

            try {
                const result = await getEvaluationMetrics();
                if (!isCurrent) {
                    return;
                }
                setMetrics(result);
                setCharts({
                    responseTimes: (result.response_time_history ?? [])
                        .filter(Number.isFinite)
                        .slice(-30)
                        .map((seconds, index) => ({
                            request: index + 1,
                            seconds,
                        })),
                    retrievalOutcomes: [
                        {
                            outcome: "Returned citations",
                            queries: result.retrieval_success_count ?? 0,
                        },
                        {
                            outcome: "No citations",
                            queries: Math.max(
                                0,
                                (result.total_queries_asked ?? 0) -
                                    (result.retrieval_success_count ?? 0)
                            ),
                        },
                    ],
                });
            } catch (error) {
                if (isCurrent) {
                    setErrorMessage(
                        error instanceof Error
                            ? error.message
                            : "Unable to load Evaluation Metrics."
                    );
                }
            } finally {
                if (isCurrent) {
                    setIsLoading(false);
                }
            }
        }

        refresh();
        return () => {
            isCurrent = false;
        };
    }, [refreshCount]);

    const totalQueries = metrics?.total_queries_asked ?? 0;
    const retrievalSuccesses = metrics?.retrieval_success_count ?? 0;
    const apiStatus = errorMessage ? "Unavailable" : metrics?.api_status ?? "Unavailable";
    const databaseStatus = metrics?.database_status ?? "Unavailable";
    const cards = [
        ["Documents Uploaded", metrics ? formatCount(metrics.total_uploaded_documents) : "Unavailable"],
        ["Documents Processed", metrics ? formatCount(metrics.total_processed_documents) : "Unavailable"],
        ["Total Chunks", metrics ? formatCount(metrics.total_chunks) : "Unavailable"],
        ["Questions Asked", metrics ? formatCount(totalQueries) : "Unavailable"],
        ["Average Response Time", formatSeconds(metrics?.average_response_time_seconds)],
        ["Retrieval Time", formatSeconds(metrics?.average_retrieval_time_seconds)],
        ["Retrieval Successes", metrics ? formatCount(retrievalSuccesses) : "Unavailable"],
        ["Retrieval Success Rate", metrics ? percent(retrievalSuccesses, totalQueries) : "Unavailable"],
        [
            "Average Citation Relevance",
            Number.isFinite(metrics?.average_similarity_score)
                ? metrics.average_similarity_score.toFixed(3)
                : "Not measured",
        ],
        ["API Status", apiStatus],
        ["Database Status", databaseStatus],
    ];
    const performanceRows = [
        { metric: "Documents Uploaded", value: cards[0][1], status: apiStatus },
        { metric: "Documents Processed", value: cards[1][1], status: apiStatus },
        { metric: "Total Chunks", value: cards[2][1], status: apiStatus },
        { metric: "Questions Asked", value: cards[3][1], status: apiStatus },
        { metric: "Average Response Time", value: cards[4][1], status: cards[4][1] === "Not measured" ? "Not measured" : "Recorded" },
        { metric: "Average Retrieval Time", value: cards[5][1], status: cards[5][1] === "Not measured" ? "Not measured" : "Recorded" },
        { metric: "Retrieval Successes", value: cards[6][1], status: apiStatus },
        { metric: "Retrieval Success Rate", value: cards[7][1], status: apiStatus },
        { metric: "Citation Accuracy", value: "Not measured", status: "Not measured" },
        { metric: "Retrieval Accuracy", value: "Not measured", status: "Not measured" },
        { metric: "API Status", value: apiStatus, status: apiStatus },
        { metric: "Database Status", value: databaseStatus, status: databaseStatus },
    ];
    const systemInfo = metrics?.system_information ?? {};
    const retrievalSummary = totalQueries
        ? `${retrievalSuccesses} of ${totalQueries} questions returned citations (${percent(retrievalSuccesses, totalQueries)}).`
        : "No question requests have been recorded by this API process.";

    return (
        <main id="main-content" className="em-page" aria-labelledby="metrics-title">
            <div className="em-page-heading">
                <div>
                    <p className="eyebrow">System health and quality</p>
                    <h2 id="metrics-title" ref={headingRef} tabIndex="-1">
                        Evaluation Metrics
                    </h2>
                    <p>
                        Current document totals, request activity, performance, and
                        service health.
                    </p>
                </div>
                <div className="em-page-actions">
                    <button
                        className="em-refresh-button"
                        type="button"
                        onClick={() => setRefreshCount((count) => count + 1)}
                        disabled={isLoading}
                        aria-label="Refresh all evaluation metrics"
                    >
                        {isLoading ? "Refreshing…" : "Refresh Metrics"}
                    </button>
                    <Link
                        className="em-action-link"
                        to="/evaluation-metrics/accessibility"
                    >
                        Accessibility
                    </Link>
                </div>
            </div>

            {errorMessage && (
                <div className="em-alert" role="alert">
                    <p>{errorMessage}</p>
                    <button
                        className="em-retry-button"
                        type="button"
                        onClick={() => setRefreshCount((count) => count + 1)}
                        disabled={isLoading}
                    >
                        Try again
                    </button>
                </div>
            )}
            {isLoading && (
                <p className="em-live-status" role="status" aria-live="polite">
                    Loading current system metrics…
                </p>
            )}

            <section className="em-section" aria-labelledby="dashboard-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Current statistics</p>
                        <h2 id="dashboard-title">Dashboard</h2>
                    </div>
                    <p>Metric descriptions are available from each card’s information control.</p>
                </div>
                <div className="em-metric-grid">
                    {cards.map(([label, value]) => (
                        <MetricCard
                            key={label}
                            label={label}
                            value={value}
                            loading={isLoading}
                        />
                    ))}
                </div>
                {metrics?.total_uploaded_documents === 0 && !isLoading && (
                    <p className="em-empty-state" role="status">
                        No documents are stored yet.{" "}
                        <Link to="/">Upload a PDF in the Research workspace</Link>.
                    </p>
                )}
            </section>

            <section className="em-section" aria-labelledby="pipeline-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">How a response is produced</p>
                        <h2 id="pipeline-title">AI Pipeline</h2>
                    </div>
                </div>
                <ol className="em-pipeline" aria-label="AI response pipeline steps">
                    {pipelineStages.map((stage, index) => (
                        <li className="em-pipeline-step" key={stage}>
                            <span className="em-stage-number" aria-hidden="true">
                                {String(index + 1).padStart(2, "0")}
                            </span>
                            <span>
                                {index === 4
                                    ? systemInfo.llm || "Configured LLM"
                                    : stage}
                            </span>
                            {index < pipelineStages.length - 1 && (
                                <span className="em-stage-arrow" aria-hidden="true">
                                    ↓
                                </span>
                            )}
                        </li>
                    ))}
                </ol>
            </section>

            <section className="em-section" aria-labelledby="charts-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Observed activity</p>
                        <h2 id="charts-title">Charts</h2>
                    </div>
                </div>
                <div className="em-chart-grid">
                    <ChartPanel
                        title="Response Time"
                        summary={
                            charts.responseTimes.length
                                ? `Showing ${charts.responseTimes.length} recent measured end-to-end response times in seconds.`
                                : "Response timings are recorded after questions are processed by this API process."
                        }
                    >
                        {charts.responseTimes.length ? (
                            <div className="em-chart">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={charts.responseTimes} accessibilityLayer>
                                        <CartesianGrid stroke="#e8eef2" strokeDasharray="3 3" />
                                        <XAxis dataKey="request" tick={{ fill: "#52677a", fontSize: 11 }} />
                                        <YAxis width={42} tick={{ fill: "#52677a", fontSize: 11 }} unit="s" />
                                        <Tooltip formatter={(value) => [`${Number(value).toFixed(3)} sec`, "Response time"]} />
                                        <Line
                                            type="monotone"
                                            dataKey="seconds"
                                            name="Response time"
                                            stroke="#315b7f"
                                            strokeWidth={3}
                                            dot={{ r: 4, fill: "#315b7f" }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <p className="em-chart-empty">No response timings are recorded yet.</p>
                        )}
                    </ChartPanel>
                    <ChartPanel
                        title="Retrieval Outcomes"
                        summary={retrievalSummary}
                    >
                        {metrics && totalQueries > 0 ? (
                            <div className="em-chart">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={charts.retrievalOutcomes} accessibilityLayer>
                                        <CartesianGrid stroke="#e8eef2" strokeDasharray="3 3" />
                                        <XAxis dataKey="outcome" tick={{ fill: "#52677a", fontSize: 10 }} />
                                        <YAxis allowDecimals={false} width={38} tick={{ fill: "#52677a", fontSize: 11 }} />
                                        <Tooltip />
                                        <Bar dataKey="queries" name="Questions" fill="#5386a7" radius={[5, 5, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <p className="em-chart-empty">Retrieval outcomes appear after the first question.</p>
                        )}
                    </ChartPanel>
                    <ChartPanel
                        title="Query Distribution"
                        summary={retrievalSummary}
                    >
                        {metrics && totalQueries > 0 ? (
                            <div className="em-chart em-chart-pie">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart accessibilityLayer>
                                        <Pie
                                            data={charts.retrievalOutcomes}
                                            dataKey="queries"
                                            nameKey="outcome"
                                            innerRadius={48}
                                            outerRadius={90}
                                            paddingAngle={3}
                                            label={({ percent: share }) =>
                                                `${(share * 100).toFixed(0)}%`
                                            }
                                        >
                                            <Cell fill="#315b7f" />
                                            <Cell fill="#a85a4a" />
                                        </Pie>
                                        <Legend verticalAlign="bottom" height={36} />
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <p className="em-chart-empty">Query distribution appears after the first question.</p>
                        )}
                    </ChartPanel>
                </div>
            </section>

            <section className="em-section" aria-labelledby="performance-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Measured values</p>
                        <h2 id="performance-title">Performance</h2>
                    </div>
                </div>
                <MetricTable
                    caption="Current service metrics and evaluation status"
                    rows={performanceRows}
                    headers={[
                        { key: "metric", label: "Metric" },
                        { key: "value", label: "Value" },
                        { key: "status", label: "Status" },
                    ]}
                />
                <p className="em-data-note">
                    Accuracy requires labeled evaluation data and is not inferred from
                    retrieval success.
                </p>
            </section>

            <section className="em-section" aria-labelledby="system-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Application configuration</p>
                        <h2 id="system-title">System Information</h2>
                    </div>
                </div>
                <dl className="em-system-grid">
                    {[
                        ["Frontend", systemInfo.frontend],
                        ["Backend", systemInfo.backend],
                        ["Database", systemInfo.database],
                        ["Embedding Model", systemInfo.embedding_model],
                        ["LLM", systemInfo.llm],
                        ["Retrieval Method", systemInfo.retrieval_method],
                    ].map(([label, value]) => (
                        <div key={label}>
                            <dt>{label}</dt>
                            <dd>{value || (isLoading ? "Loading…" : "Unavailable")}</dd>
                        </div>
                    ))}
                </dl>
            </section>

            <section className="em-section" aria-labelledby="queries-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Activity privacy</p>
                        <h2 id="queries-title">Recent Queries</h2>
                    </div>
                </div>
                <MetricTable
                    caption="Recent legal research queries"
                    rows={[]}
                    headers={[
                        { key: "question", label: "Question" },
                        { key: "chunks", label: "Retrieved Chunks" },
                        { key: "similarity", label: "Similarity" },
                        { key: "responseTime", label: "Response Time" },
                    ]}
                />
            </section>
        </main>
    );
}

const accessibilityChecks = [
    {
        label: "Keyboard Navigation Status",
        status: "Implemented",
        passed: true,
        detail: "Navigation links, buttons, tooltips, and scrollable tables are keyboard operable.",
    },
    {
        label: "Screen Reader Compatibility",
        status: "Semantic labels provided",
        passed: true,
        detail: "Page landmarks, headings, table headers, chart descriptions, and status announcements are present.",
    },
    {
        label: "Color Contrast Compliance",
        status: "Manual verification required",
        passed: false,
        detail: "Theme colors need a full contrast audit across all states and displays.",
    },
    {
        label: "Responsive Layout Status",
        status: "Responsive",
        passed: true,
        detail: "Metric cards and charts adapt to narrower viewports.",
    },
    {
        label: "ARIA Support",
        status: "Implemented",
        passed: true,
        detail: "ARIA labels and live status announcements supplement native semantics.",
    },
    {
        label: "Focus Management",
        status: "Page heading receives focus",
        passed: true,
        detail: "Navigating to an evaluation page moves focus to its main heading.",
    },
    {
        label: "Form Accessibility",
        status: "Existing inputs labeled",
        passed: true,
        detail: "Research inputs have associated labels and announced validation status.",
    },
];

export function AccessibilityPage() {
    const headingRef = usePageFocus();
    const score = Math.round(
        (accessibilityChecks.filter((check) => check.passed).length /
            accessibilityChecks.length) *
            100
    );
    const accessibilityRows = accessibilityChecks.map((check) => ({
        metric: check.label,
        value: check.detail,
        status: check.passed ? "Passed" : "Needs review",
    }));

    return (
        <main id="main-content" className="em-page" aria-labelledby="accessibility-title">
            <div className="em-page-heading">
                <div>
                    <p className="eyebrow">Inclusive access and usability</p>
                    <h2 id="accessibility-title" ref={headingRef} tabIndex="-1">
                        Accessibility
                    </h2>
                    <p>Accessibility implementation checks and recommended follow-up.</p>
                </div>
                <Link className="em-action-link" to="/evaluation-metrics">
                    Back to Evaluation Metrics
                </Link>
            </div>

            <section className="em-section" aria-labelledby="accessibility-score-title">
                <div className="em-accessibility-score">
                    <div>
                        <p className="eyebrow">Implementation checklist score</p>
                        <h2 id="accessibility-score-title">Overall Accessibility Score</h2>
                        <p
                            className="em-score-value"
                            aria-label={`${score} out of 100, calculated from implementation checklist`}
                        >
                            {score}<span>/100</span>
                        </p>
                    </div>
                    <p>
                        Calculated from the checks below. This estimate is not a
                        certified WCAG audit and should be followed by manual testing.
                    </p>
                </div>
            </section>

            <section className="em-section" aria-labelledby="accessibility-status-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Implementation status</p>
                        <h2 id="accessibility-status-title">Accessibility Status</h2>
                    </div>
                </div>
                <dl className="em-system-grid">
                    {accessibilityChecks.map((check) => (
                        <div key={check.label}>
                            <dt>{check.label}</dt>
                            <dd>{check.status}</dd>
                        </div>
                    ))}
                </dl>
            </section>

            <section className="em-section" aria-labelledby="accessibility-checklist-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Review results</p>
                        <h2 id="accessibility-checklist-title">Accessibility Checklist</h2>
                    </div>
                </div>
                <MetricTable
                    caption="Accessibility implementation checklist"
                    rows={accessibilityRows}
                    headers={[
                        { key: "metric", label: "Checklist Item" },
                        { key: "value", label: "Review" },
                        { key: "status", label: "Status" },
                    ]}
                />
            </section>

            <section className="em-section" aria-labelledby="accessibility-recommendations-title">
                <div className="em-section-heading">
                    <div>
                        <p className="eyebrow">Recommended next steps</p>
                        <h2 id="accessibility-recommendations-title">
                            Accessibility Recommendations
                        </h2>
                    </div>
                </div>
                <ul className="em-suggestions">
                    {!accessibilityChecks.find(
                        (check) => check.label === "Color Contrast Compliance"
                    ).passed && (
                        <li>
                            Audit text, controls, charts, and focus indicators for WCAG
                            contrast in every visual state.
                        </li>
                    )}
                    <li>
                        Test navigation, metric cards, tables, forms, and chart
                        summaries with keyboard-only input and screen readers.
                    </li>
                    <li>
                        Verify responsive layouts at narrow widths and browser zoom up
                        to 200%.
                    </li>
                </ul>
            </section>
        </main>
    );
}

export default EvaluationMetrics;
