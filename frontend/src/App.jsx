import { useState } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";
import DocumentList from "./components/DocumentList";
import "./App.css";

function App() {
    const [uploadedDocument, setUploadedDocument] = useState(null);

    return (
        <main className="app-container">
            <header className="header">
                <span className="brand-mark" aria-hidden="true">LI</span>
                <p className="eyebrow">Legal research workspace</p>
                <h1>LexIntel AI</h1>
                <p>
                    Ask questions and explore answers grounded in your legal
                    documents.
                </p>
            </header>

            <div className="workspace-grid">
                <aside className="workspace-sidebar">
                    <section className="card upload-card">
                        <Upload onUploaded={setUploadedDocument} />
                    </section>
                    <section className="card library-card">
                        <DocumentList uploadedDocument={uploadedDocument} />
                    </section>
                </aside>

                <section className="card chat-card">
                    <Chat />
                </section>
            </div>
        </main>
    );
}

export default App;
