function Citation({ data }) {
    const hasValue = (value) =>
        value !== null &&
        value !== undefined &&
        String(value).trim() !== "";

    return (
        <div className="citation-card">
            {hasValue(data.source) && (
                <h4 className="citation-title">
                    📄 {data.source}
                </h4>
            )}

            {(hasValue(data.page) || hasValue(data.section)) && (
                <div className="citation-details">
                    {hasValue(data.page) && (
                        <p>
                            <b>Page:</b> {data.page}
                        </p>
                    )}
                    {hasValue(data.section) && (
                        <p>
                            <b>Section:</b> {data.section}
                        </p>
                    )}
                </div>
            )}

            {hasValue(data.quote) && (
                <blockquote className="citation-quote">
                    {data.quote}
                </blockquote>
            )}
        </div>
    );
}


export default Citation;