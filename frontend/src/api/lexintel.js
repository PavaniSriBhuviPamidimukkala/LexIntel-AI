const API_URL = "https://cuddly-space-pancake-69pw9v4r74wpc9j9-8000.app.github.dev";


// Upload PDF
export async function uploadDocument(file) {

    const formData = new FormData();

    formData.append("file", file);


    const response = await fetch(
        `${API_URL}/documents/upload`,
        {
            method: "POST",
            body: formData,
        }
    );


    if (!response.ok) {
        throw new Error("Upload failed");
    }


    return response.json();
}



// Ask legal question
export async function askQuestion(question) {

    const response = await fetch(
        `${API_URL}/ask/?question=${encodeURIComponent(question)}`,
        {
            method: "POST",
        }
    );


    if (!response.ok) {
        throw new Error("Question failed");
    }


    return response.json();
}