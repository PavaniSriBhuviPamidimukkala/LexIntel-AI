import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDocuments } from "../api/lexintel";

function Dashboard() {
    const [documents, setDocuments] = useState([]);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        let active = true;
        getDocuments()
            .then((result) => {
                if (active) {
                    setDocuments(result);
                }
            })
            .catch((error) => {
                if (active) {
                    setErrorMessage(
                        error instanceof Error
                            ? error.message
                            : "Unable to load document activity."
                    );
                }
            });
        return () => {
            active = false;
        };
    }, []);

    const recentDocument = [...documents].sort(
        (left, right) =>
            new Date(right.created_at).getTime() -
            new Date(left.created_at).getTime()
    )[0];
    const quickActions = [
        ["/upload", "Upload Document", "Add a legal PDF to your library."],
        ["/documents", "Document History", "Browse uploaded documents."],
        ["/ask", "Ask AI", "Ask questions grounded in your documents."],
        ["/evaluation-metrics", "Evaluation Metrics", "Review system activity."],
    ];

    return (
        <main id="main-content" className="page-shell" aria-labelledby="dashboard-title">
            <section className="dashboard-welcome">
                <p className="eyebrow">Your legal research workspace</p>
                <h1 id="dashboard-title">Welcome to LexIntel AI</h1>
                <p className="page-intro">
                    Upload legal documents, explore your library, and get
                    evidence-grounded answers.
                </p>
            </section>

            <section className="summary-grid" aria-label="Workspace summary">
                <article className="card summary-card">
                    <p className="eyebrow">Your library</p>
                    <p className="summary-value">
                        {errorMessage ? "—" : documents.length}
                    </p>
                    <p>Uploaded documents</p>
                </article>
                <article className="card summary-card">
                    <p className="eyebrow">Recent activity</p>
                    <p className="summary-highlight">
                        {recentDocument?.title || (errorMessage ? "Unavailable" : "No uploads yet")}
                    </p>
                    <p>
                        {recentDocument?.created_at
                            ? `Uploaded ${new Date(recentDocument.created_at).toLocaleDateString()}`
                            : errorMessage || "Your latest uploaded document will appear here."}
                    </p>
                </article>
            </section>

            <section className="dashboard-actions" aria-labelledby="actions-title">
                <div className="page-section-heading">
                    <div>
                        <p className="eyebrow">Get started</p>
                        <h2 id="actions-title">Quick actions</h2>
                    </div>
                </div>
                <div className="action-grid">
                    {quickActions.map(([href, title, description]) => (
                        <Link className="card action-card" to={href} key={href}>
                            <h3>{title}</h3>
                            <p>{description}</p>
                            <span aria-hidden="true">Go to page →</span>
                        </Link>
                    ))}
                </div>
            </section>
        </main>
    );
}

export default Dashboard;
