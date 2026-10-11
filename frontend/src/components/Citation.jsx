function Citation({ data, index, showEvidence = true }) {
    if (!data) {
        return null;
    }

    const hasValue = (value) =>
        value !== null &&
        value !== undefined &&
        String(value).trim() !== "";

    return (
        <article className="citation-card">
            <div className="citation-card-header">
                <span className="citation-card-icon" aria-hidden="true">§</span>
                <span className="citation-type">Retrieved source</span>
                {index !== undefined && (
                    <span className="citation-index">Source {index}</span>
                )}
            </div>
            {hasValue(data.source) && (
                <h4 className="citation-title">
                    {data.source}
                </h4>
            )}

            {(hasValue(data.page) ||
                hasValue(data.section) ||
                hasValue(data.chapter) ||
                hasValue(data.category)) && (
                <dl className="citation-details">
                    {hasValue(data.section) && (
                        <div className="citation-detail">
                            <dt>Section</dt>
                            <dd>{data.section}</dd>
                        </div>
                    )}
                    {hasValue(data.page) && (
                        <div className="citation-detail">
                            <dt>Page</dt>
                            <dd>{data.page}</dd>
                        </div>
                    )}
                    {hasValue(data.chapter) && (
                        <div className="citation-detail">
                            <dt>Chapter</dt>
                            <dd>{data.chapter}</dd>
                        </div>
                    )}
                    {hasValue(data.category) && (
                        <div className="citation-detail">
                            <dt>Type</dt>
                            <dd>{data.category}</dd>
                        </div>
                    )}
                </dl>
            )}

            {showEvidence && hasValue(data.quote) && (
                <details className="citation-evidence">
                    <summary>
                        <span>View evidence snippet</span>
                        <span className="expand-indicator" aria-hidden="true">+</span>
                    </summary>
                    <blockquote className="citation-quote">
                        {data.quote}
                    </blockquote>
                </details>
            )}
            {!hasValue(data.source) &&
                !hasValue(data.page) &&
                !hasValue(data.section) &&
                !hasValue(data.quote) && (
                    <p className="citation-empty">
                        Source details are not available.
                    </p>
                )}
        </article>
    );
}


export default Citation;