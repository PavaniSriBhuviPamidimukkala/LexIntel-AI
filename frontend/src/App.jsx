import { useState } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";
import "./App.css";

function App() {
    const [uploadedDocument, setUploadedDocument] = useState(null);

    return (
        <div className="app-container">
            <header className="header">
                <h1>⚖️ LexIntel AI</h1>
                <p>AI-powered Legal Document Intelligence Platform</p>
            </header>

            <section className="card">
                <Upload onUploaded={setUploadedDocument} />

                {uploadedDocument && (
                    <div className="answer-box">
                        <h3>📄 Uploaded Document</h3>
                        <p>{uploadedDocument.title}</p>
                    </div>
                )}
            </section>

            <section className="card">
                <Chat />
            </section>
        </div>
    );
}

export default App;
