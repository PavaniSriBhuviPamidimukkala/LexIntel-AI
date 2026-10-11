function Citation({ data, showEvidence = true }) {
    if (!data) {
        return null;
    }

    const hasValue = (value) =>
        value !== null &&
        value !== undefined &&
        String(value).trim() !== "";

    return (
        <article className="citation-card">
            {hasValue(data.source) && (
                <h4 className="citation-title">
                    {data.source}
                </h4>
            )}

            {(hasValue(data.page) || hasValue(data.section)) && (
                <dl className="citation-details">
                    {hasValue(data.page) && (
                        <div className="citation-detail">
                            <dt>Page</dt>
                            <dd>{data.page}</dd>
                        </div>
                    )}
                    {hasValue(data.section) && (
                        <div className="citation-detail">
                            <dt>Section</dt>
                            <dd>{data.section}</dd>
                        </div>
                    )}
                </dl>
            )}

            {showEvidence && hasValue(data.quote) && (
                <details className="citation-evidence" open>
                    <summary>Evidence snippet</summary>
                    <blockquote className="citation-quote">
                        {data.quote}
                    </blockquote>
                </details>
            )}
        </article>
    );
}


export default Citation;