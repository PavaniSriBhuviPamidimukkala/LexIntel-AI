const API_URL =
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000";

const QUESTION_ERROR_MESSAGE =
    "We couldn't get an answer right now. Please try again.";

function getQuestionErrorMessage(errorBody) {
    const detailMessage =
        typeof errorBody?.detail === "string"
            ? errorBody.detail
            : Array.isArray(errorBody?.detail)
                ? errorBody.detail
                    .map((item) =>
                        typeof item === "string" ? item : item?.msg
                    )
                    .filter((item) =>
                        typeof item === "string" && item.trim()
                    )
                    .join(" ")
                : null;

    if (detailMessage) {
        return detailMessage;
    }

    return typeof errorBody?.message === "string"
        ? errorBody.message
        : QUESTION_ERROR_MESSAGE;
}


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
        let errorBody;

        try {
            errorBody = JSON.parse(await response.text());
        } catch {
            errorBody = null;
        }

        throw new Error(getQuestionErrorMessage(errorBody));
    }


    return response.json();
}