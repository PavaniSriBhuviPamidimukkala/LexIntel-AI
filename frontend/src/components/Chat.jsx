import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion } from "../api/lexintel";
import Citation from "./Citation";

const CONNECTION_ERROR_MESSAGE =
    "We couldn't connect to the legal research service. Please check your connection and try again.";
const REQUEST_ERROR_MESSAGE =
    "We couldn't get an answer right now. Please try again.";

function getChatErrorMessage(error) {
    if (error instanceof TypeError) {
        return CONNECTION_ERROR_MESSAGE;
    }

    return error instanceof Error ? error.message : REQUEST_ERROR_MESSAGE;
}

function Chat() {
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [citations, setCitations] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const answerRef = useRef(null);
    const scrollToAnswer = useRef(false);

    useEffect(() => {
        if (!isLoading && scrollToAnswer.current && answer) {
            answerRef.current?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
            scrollToAnswer.current = false;
        }
    }, [answer, isLoading]);

    async function handleAsk() {
        if (!question.trim()) {
            setErrorMessage("Enter a legal question to continue.");
            setSuccessMessage("");
            return;
        }

        setErrorMessage("");
        setSuccessMessage("");

        try {
            setIsLoading(true);

            const result = await askQuestion(question);
            setAnswer(result.answer);
            setCitations(result.citations || []);
            scrollToAnswer.current = true;
            setSuccessMessage("Your answer is ready.");
        } catch (error) {
            setErrorMessage(getChatErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div>
            <h2>⚖️ Ask LexIntel AI</h2>
            <p>Ask questions based on your uploaded legal documents.</p>

            <textarea
                rows="5"
                placeholder="Example: What is a contract of sale?"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
            />

            <br />

            <button onClick={handleAsk} disabled={isLoading}>
                {isLoading ? (
                    <>
                        <span className="loading-spinner" aria-hidden="true" />
                        Analyzing...
                    </>
                ) : (
                    "Ask Legal AI"
                )}
            </button>

            {errorMessage && (
                <p className="status-message status-error" role="alert">
                    {errorMessage}
                </p>
            )}

            {successMessage && !isLoading && (
                <p className="status-message status-success" role="status">
                    {successMessage}
                </p>
            )}

            {isLoading && (
                <p className="status-message status-loading" role="status">
                    Please wait while we prepare your answer.
                </p>
            )}

            {answer && (
                <div className="answer-box" ref={answerRef}>
                    <h3>🤖 LexIntel Answer</h3>
                    <ReactMarkdown>{answer}</ReactMarkdown>

                    {citations.length > 0 && (
                        <>
                            <h3>📚 Sources</h3>
                            {citations.map((citation, index) => (
                                <Citation key={index} data={citation} />
                            ))}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export default Chat;
