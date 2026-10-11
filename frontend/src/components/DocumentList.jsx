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
    }, []);

    const displayedDocuments = uploadedDocument
        ? [
            uploadedDocument,
            ...documents.filter(
                (document) => document.id !== uploadedDocument.id
            ),
        ]
        : documents;
    const visibleError = uploadedDocument ? "" : errorMessage;

    return (
        <section className="document-list" aria-labelledby="documents-heading">
            <div className="section-heading">
                <div>
                    <p className="eyebrow">Your library</p>
                    <h2 id="documents-heading">Uploaded documents</h2>
                </div>
                {displayedDocuments.length > 0 && (
                    <span className="document-count">
                        {displayedDocuments.length}{" "}
                        {displayedDocuments.length === 1 ? "document" : "documents"}
                    </span>
                )}
            </div>

            {isLoading && (
                <p className="status-message status-loading" role="status">
                    Loading your document library...
                </p>
            )}

            {visibleError && (
                <p className="status-message status-error" role="alert">
                    {visibleError}
                </p>
            )}

            {!isLoading && !visibleError && displayedDocuments.length === 0 && (
                <p className="empty-state">
                    Uploaded legal documents will appear here.
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
                                        {document.category && (
                                            <span>{document.category}</span>
                                        )}
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
