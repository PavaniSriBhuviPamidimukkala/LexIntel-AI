import { useState } from "react";

import Upload from "./components/Upload";
import Chat from "./components/Chat";


function App() {

    const [document, setDocument] = useState(null);


    return (

        <div style={{
            maxWidth:"900px",
            margin:"40px auto",
            fontFamily:"Arial"
        }}>

            <h1>
                ⚖️ LexIntel AI
            </h1>

            <p>
                AI-powered Legal Document Intelligence Platform
            </p>


            <hr />


            <Upload
                onUploaded={
                    setDocument
                }
            />


            {
                document &&
                <div>

                    <hr />

                    <h3>
                        Uploaded Document
                    </h3>

                    <p>
                        {document.title}
                    </p>

                </div>
            }


            <hr />


            <Chat />


        </div>

    );
}


export default App;