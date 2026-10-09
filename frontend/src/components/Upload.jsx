import { useState } from "react";
import { uploadDocument } from "../api/lexintel";


function Upload({ onUploaded }) {

    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);


    async function handleUpload() {

        if (!file) {
            alert("Please select a PDF");
            return;
        }


        try {

            setLoading(true);

            const result = await uploadDocument(file);

            alert("Document uploaded successfully");

            onUploaded(result);

        } catch(error) {

            alert(error.message);

        } finally {

            setLoading(false);

        }
    }


    return (
        <div>

            <h2>
                Upload Legal Document
            </h2>


            <input
                type="file"
                accept="application/pdf"
                onChange={
                    e => setFile(e.target.files[0])
                }
            />


            <button
                onClick={handleUpload}
                disabled={loading}
            >
                {
                    loading
                    ? "Uploading..."
                    : "Upload PDF"
                }
            </button>

        </div>
    );
}


export default Upload;