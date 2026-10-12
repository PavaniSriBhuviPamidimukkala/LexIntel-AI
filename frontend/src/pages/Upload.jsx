import { useState } from "react";
import ExistingUpload from "../components/Upload";

const processingStages = [
    "Text extraction",
    "Cleaning",
    "Chunking",
    "Embedding generation",
    "Vector storage",
];

function Upload() {
    const [uploaded, setUploaded] = useState(false);

    return (
        <main id="main-content" className="page-shell" aria-labelledby="upload-title">
            <div className="page-heading">
                <div>
                    <p className="eyebrow">Add to your research library</p>
                    <h1 id="upload-title">Upload a document</h1>
                    <p className="page-intro">
                        Upload a PDF to extract and index its legal content.
                    </p>
                </div>
            </div>
            <div className="upload-page-grid">
                <section className="card">
                    <ExistingUpload
                        onUploadStarted={() => setUploaded(false)}
                        onUploaded={() => setUploaded(true)}
                    />
                </section>
                <section className="card processing-card" aria-labelledby="processing-title">
                    <p className="eyebrow">Document processing</p>
                    <h2 id="processing-title">Processing stages</h2>
                    <p className="component-description">
                        The existing upload API processes documents through these
                        stages before returning success.
                    </p>
                    <ol className="processing-stages">
                        {processingStages.map((stage, index) => (
                            <li
                                className={uploaded ? "stage-complete" : ""}
                                key={stage}
                            >
                                <span aria-hidden="true">
                                    {uploaded ? "✓" : String(index + 1).padStart(2, "0")}
                                </span>
                                {stage}
                            </li>
                        ))}
                    </ol>
                    {!uploaded && (
                        <p className="input-hint">
                            Stage-by-stage progress is not currently returned by
                            the backend.
                        </p>
                    )}
                </section>
            </div>
        </main>
    );
}

export default Upload;
