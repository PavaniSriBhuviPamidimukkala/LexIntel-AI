import { useState } from "react";
import { uploadDocument } from "../api/lexintel";

function Upload({ onUploaded }) {
    const [file, setFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    function handleFileChange(event) {
        const selectedFile = event.target.files?.[0] ?? null;

        setErrorMessage("");
        setSuccessMessage("");

        if (!selectedFile) {
            setFile(null);
            return;
        }

        const hasPdfExtension =
            selectedFile.name.toLowerCase().endsWith(".pdf");
        const hasPdfMimeType =
            !selectedFile.type || selectedFile.type === "application/pdf";

        if (!hasPdfExtension || !hasPdfMimeType) {
            setFile(null);
            setErrorMessage("Please choose a PDF file to upload.");
            event.target.value = "";
            return;
        }

        setFile(selectedFile);
    }

    async function handleUpload() {
        if (!file) {
            setErrorMessage("Please choose a PDF file before uploading.");
            setSuccessMessage("");
            return;
        }

        try {
            setErrorMessage("");
            setSuccessMessage("");
            setIsUploading(true);

            const result = await uploadDocument(file);
            onUploaded(result);
            setSuccessMessage("Document uploaded successfully.");
        } catch {
            setErrorMessage(
                "We couldn't upload this document. Please try again."
            );
        } finally {
            setIsUploading(false);
        }
    }

    return (
        <div>
            <h2>📄 Upload Legal Document</h2>
            <p>
                Upload Acts, contracts, or legal PDFs for AI-powered analysis.
            </p>

            <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                disabled={isUploading}
            />

            {file && <p>Selected: {file.name}</p>}

            {errorMessage && (
                <p className="status-message status-error" role="alert">
                    {errorMessage}
                </p>
            )}

            {successMessage && (
                <p className="status-message status-success" role="status">
                    {successMessage}
                </p>
            )}

            <button
                onClick={handleUpload}
                disabled={isUploading || !file}
            >
                {isUploading ? (
                    <>
                        <span className="loading-spinner" aria-hidden="true" />
                        Processing PDF...
                    </>
                ) : (
                    "Upload Document"
                )}
            </button>
        </div>
    );
}

export default Upload;
