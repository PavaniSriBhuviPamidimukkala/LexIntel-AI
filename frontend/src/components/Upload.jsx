import { useRef, useState } from "react";
import { uploadDocument } from "../api/lexintel";

function Upload({ onUploaded }) {
    const [file, setFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    function selectFile(selectedFile) {
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
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
            return;
        }

        setFile(selectedFile);
    }

    function handleFileChange(event) {
        selectFile(event.target.files?.[0] ?? null);
    }

    function handleDrop(event) {
        event.preventDefault();
        setIsDragging(false);
        selectFile(event.dataTransfer.files?.[0] ?? null);
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
            setFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        } catch {
            setErrorMessage(
                "We couldn't upload this document. Please try again."
            );
        } finally {
            setIsUploading(false);
        }
    }

    return (
        <div className="upload-workspace">
            <div className="component-heading">
                <span className="section-icon" aria-hidden="true">↑</span>
                <div>
                    <p className="eyebrow">Add to your workspace</p>
                    <h2>Upload a document</h2>
                </div>
            </div>
            <p className="component-description">
                Upload an Act, contract, or other legal PDF to make it
                searchable.
            </p>

            <label
                className={`file-dropzone${isDragging ? " is-dragging" : ""}`}
                htmlFor="legal-document-file"
                onDragEnter={(event) => {
                    event.preventDefault();
                    setIsDragging(true);
                }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget)) {
                        setIsDragging(false);
                    }
                }}
                onDrop={handleDrop}
            >
                <span className="upload-symbol" aria-hidden="true">PDF</span>
                <span className="dropzone-title">
                    {file ? "Document selected" : "Choose a PDF to upload"}
                </span>
                <span className="dropzone-hint">
                    {file ? "Select another file to replace it" : "Browse files or drag and drop"}
                </span>
                <input
                    ref={fileInputRef}
                    id="legal-document-file"
                    className="visually-hidden"
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={handleFileChange}
                    disabled={isUploading}
                />
            </label>

            {file && (
                <div className="selected-file" aria-live="polite">
                    <span className="selected-file-icon" aria-hidden="true">
                        PDF
                    </span>
                    <span className="selected-file-name" title={file.name}>
                        {file.name}
                    </span>
                    <span className="selected-file-size">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                </div>
            )}

            {errorMessage && (
                <p className="status-message status-error" role="alert" aria-live="assertive">
                    {errorMessage}
                </p>
            )}

            {successMessage && (
                <p className="status-message status-success" role="status">
                    {successMessage}
                </p>
            )}

            <button
                className="upload-button"
                onClick={handleUpload}
                disabled={isUploading || !file}
            >
                {isUploading ? (
                    <>
                        <span className="loading-spinner" aria-hidden="true" />
                        Processing document...
                    </>
                ) : (
                    <>
                        Upload to library
                        <span aria-hidden="true">→</span>
                    </>
                )}
            </button>
        </div>
    );
}

export default Upload;
