import DocumentList from "../components/DocumentList";

function Documents() {
    return (
        <main id="main-content" className="page-shell documents-page">
            <div className="page-heading">
                <div>
                    <p className="eyebrow">Your research library</p>
                    <h1>Document History</h1>
                    <p className="page-intro">
                        Review the documents uploaded to the LexIntel workspace.
                    </p>
                </div>
            </div>
            <section className="card">
                <DocumentList />
            </section>
        </main>
    );
}

export default Documents;
