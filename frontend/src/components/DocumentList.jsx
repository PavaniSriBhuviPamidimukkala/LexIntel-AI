import { useEffect, useState } from "react";
import { getDocuments } from "../api/lexintel";

function formatUploadDate(value) {
    if (!value) {
        return null;
    }

    const date = new Date(value);
    return Number.isNaN(date.getTime())
        ? null
        : date.toLocaleString(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
        });
}

function DocumentList({ uploadedDocument }) {
    const [documents, setDocuments] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState("");
    const [refreshIndex, setRefreshIndex] = useState(0);
    const [search, setSearch] = useState("");

    useEffect(() => {
        let isMounted = true;

        async function loadDocuments() {
            try {
                const result = await getDocuments();
                if (isMounted) {
                    setDocuments(result);
                    setErrorMessage("");
                }
            } catch (error) {
                if (isMounted) {
                    setErrorMessage(
                        error instanceof Error
                            ? error.message
                            : "We couldn't load the uploaded documents."
                    );
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        loadDocuments();

        return () => {
            isMounted = false;
        };
    }, [refreshIndex]);

    const allDocuments = uploadedDocument
        ? [
            uploadedDocument,
            ...documents.filter(
                (document) => document.id !== uploadedDocument.id
            ),
        ]
        : documents;
    const displayedDocuments = allDocuments.filter((document) =>
        `${document.title} ${document.category ?? ""}`
            .toLowerCase()
            .includes(search.trim().toLowerCase())
    );
    const visibleError = uploadedDocument ? "" : errorMessage;

    return (
        <section className="document-list" aria-labelledby="documents-heading">
            <div className="section-heading">
                <div>
                    <p className="eyebrow">Your research library</p>
                    <h2 id="documents-heading">Documents</h2>
                </div>
                <span className="document-count" aria-label={`${allDocuments.length} documents`}>
                    {allDocuments.length}
                </span>
            </div>
            <label className="document-search-label" htmlFor="document-search">
                Search documents
            </label>
            <input
                id="document-search"
                className="document-search"
                type="search"
                placeholder="Search by document name or category"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
            />

            {isLoading && (
                <p className="status-message status-loading" role="status">
                    <span className="loading-spinner loading-spinner-dark" aria-hidden="true" />
                    Loading your document library...
                </p>
            )}

            {visibleError && (
                <div className="library-error" role="alert">
                    <p className="status-message status-error">{visibleError}</p>
                    <button
                        className="text-button"
                        onClick={() => {
                            setIsLoading(true);
                            setRefreshIndex((index) => index + 1);
                        }}
                        disabled={isLoading}
                    >
                        Try again
                    </button>
                </div>
            )}

            {!isLoading && !visibleError && displayedDocuments.length === 0 && (
                <p className="empty-state">
                    <span className="empty-state-icon" aria-hidden="true">▤</span>
                    {allDocuments.length === 0 ? (
                        <>
                            <span>Your library is ready.</span>
                            <span>Uploaded legal documents will appear here.</span>
                        </>
                    ) : (
                        <>
                            <span>No matching documents.</span>
                            <span>Try a different name or category.</span>
                        </>
                    )}
                </p>
            )}

            {displayedDocuments.length > 0 && (
                <ul className="document-list-items">
                    {displayedDocuments.map((document) => {
                        const uploadDate = formatUploadDate(document.created_at);

                        return (
                            <li className="document-list-item" key={document.id}>
                                <span className="document-icon" aria-hidden="true">
                                    PDF
                                </span>
                                <div className="document-info">
                                    <h3 title={document.title}>{document.title}</h3>
                                    <div className="document-metadata">
                                        <span className="metadata-tag">Stored</span>
                                        {document.category && (
                                            <span className="metadata-tag">
                                                {document.category}
                                            </span>
                                        )}
                                        <span>Document #{document.id}</span>
                                        {uploadDate && (
                                            <span>Uploaded {uploadDate}</span>
                                        )}
                                    </div>
                                </div>
                            </li>
                        );
                    })}
                </ul>
            )}
        </section>
    );
}

export default DocumentList;
