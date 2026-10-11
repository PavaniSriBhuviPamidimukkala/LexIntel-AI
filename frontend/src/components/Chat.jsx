import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion } from "../api/lexintel";
import Citation from "./Citation";

const CONNECTION_ERROR_MESSAGE =
    "We couldn't connect to the legal research service. Please check your connection and try again.";
const REQUEST_ERROR_MESSAGE =
    "We couldn't get an answer right now. Please try again.";

const ANSWER_SECTIONS = [
    ["legalAnswer", "Legal Answer"],
    ["explanation", "Explanation"],
    ["keyLegalPoints", "Key Legal Points"],
    ["sources", "Sources"],
    ["evidence", "Evidence"],
];

function parseAnswerSections(answer) {
    const sections = {};
    const sectionPattern =
        /^\s*(?:#{1,6}\s*)?(Legal Answer|Explanation|Key Legal Points|Sources|Evidence):?\s*$/i;
    let currentSection = null;

    for (const line of answer.split("\n")) {
        const heading = line.match(sectionPattern);
        if (heading) {
            currentSection = ANSWER_SECTIONS.find(
                ([, title]) => title.toLowerCase() === heading[1].toLowerCase()
            )?.[0];
            sections[currentSection] = [];
        } else if (currentSection) {
            sections[currentSection].push(line);
        }
    }

    if (Object.keys(sections).length === 0) {
        return null;
    }

    return Object.fromEntries(
        Object.entries(sections).map(([key, lines]) => [
            key,
            lines.join("\n").trim(),
        ])
    );
}

function getChatErrorMessage(error) {
    if (error instanceof TypeError) {
        return CONNECTION_ERROR_MESSAGE;
    }

    return error instanceof Error ? error.message : REQUEST_ERROR_MESSAGE;
}

function Chat() {
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [askedQuestion, setAskedQuestion] = useState("");
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
        const submittedQuestion = question.trim();

        try {
            setIsLoading(true);

            const result = await askQuestion(question);
            setAnswer(result.answer);
            setAskedQuestion(submittedQuestion);
            setCitations(result.citations || []);
            scrollToAnswer.current = true;
            setSuccessMessage("Your answer is ready.");
        } catch (error) {
            setErrorMessage(getChatErrorMessage(error));
        } finally {
            setIsLoading(false);
        }
    }

    const answerSections = answer ? parseAnswerSections(answer) : null;
    const visibleAnswer = answerSections
        ? [
            ["legalAnswer", "Legal Answer"],
            ["explanation", "Explanation"],
            ["keyLegalPoints", "Key Legal Points"],
        ].filter(([key]) => answerSections[key])
        : null;
    const evidenceCitations = citations.filter(
        (citation) =>
            typeof citation.quote === "string" && citation.quote.trim()
    );

    return (
        <div className="chat-workspace">
            <div className="chat-heading">
                <p className="eyebrow">Your legal research assistant</p>
                <h2>Ask LexIntel AI</h2>
                <p>
                    Ask a question about your documents and receive a
                    structured, evidence-grounded response.
                </p>
            </div>

            <form
                className="question-form"
                onSubmit={(event) => {
                    event.preventDefault();
                    handleAsk();
                }}
            >
                <label className="input-label" htmlFor="legal-question">
                    Your question
                </label>
                <textarea
                    id="legal-question"
                    aria-describedby="question-hint"
                    rows="5"
                    maxLength={2000}
                    placeholder="Example: What remedies are available for breach of contract?"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                />
                <div className="question-form-footer">
                    <span id="question-hint" className="input-hint">
                        Answers are limited to evidence in your uploaded
                        documents.
                    </span>
                    <span className="character-count">
                        {question.length}/2000
                    </span>
                </div>
                <button
                    className="ask-button"
                    type="submit"
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <>
                            <span className="loading-spinner" aria-hidden="true" />
                            Reviewing documents...
                        </>
                    ) : (
                        <>
                            Ask question
                            <span aria-hidden="true">→</span>
                        </>
                    )}
                </button>
            </form>

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
                <div className="chat-loading" role="status" aria-live="polite">
                    <span className="loading-spinner loading-spinner-dark" aria-hidden="true" />
                    <div>
                        <strong>Reviewing your documents</strong>
                        <span>Finding relevant passages and preparing a cited answer.</span>
                    </div>
                </div>
            )}

            {answer && (
                <section
                    className="conversation-result"
                    ref={answerRef}
                    aria-label="Latest answer"
                >
                    <article className="question-message">
                        <span className="message-label">Your question</span>
                        <p>{askedQuestion}</p>
                    </article>

                    <article className="answer-message">
                        <div className="answer-message-heading">
                            <span className="assistant-mark" aria-hidden="true">
                                LI
                            </span>
                            <div>
                                <span className="message-label">LexIntel AI</span>
                                <span className="grounding-note">
                                    Grounded in retrieved evidence
                                </span>
                            </div>
                        </div>

                        <div className="answer-content">
                            {visibleAnswer?.length > 0 ? (
                                visibleAnswer.map(([key, title]) => (
                                    <section
                                        className="answer-section"
                                        key={key}
                                    >
                                        <h3>{title}</h3>
                                        <ReactMarkdown>
                                            {answerSections[key]}
                                        </ReactMarkdown>
                                    </section>
                                ))
                            ) : (
                                <ReactMarkdown>{answer}</ReactMarkdown>
                            )}
                        </div>

                        {citations.length > 0 && (
                            <div className="citation-results">
                                <section className="source-section">
                                    <div className="result-section-heading">
                                        <h3>Sources</h3>
                                        <span>
                                            {citations.length}{" "}
                                            {citations.length === 1
                                                ? "source"
                                                : "sources"}
                                        </span>
                                    </div>
                                    <div className="citation-list">
                                        {citations.map((citation, index) => (
                                            <Citation
                                                key={
                                                    citation.chunk_id ??
                                                    `${citation.source}-${index}`
                                                }
                                                data={citation}
                                                index={index + 1}
                                                showEvidence={false}
                                            />
                                        ))}
                                    </div>
                                </section>

                                {evidenceCitations.length > 0 && (
                                    <section className="evidence-section">
                                        <div className="result-section-heading">
                                            <h3>Evidence</h3>
                                        </div>
                                        <div className="evidence-list">
                                            {evidenceCitations.map(
                                                (citation, index) => (
                                                    <article
                                                        className="evidence-card"
                                                        key={
                                                            citation.chunk_id ??
                                                            `${citation.source}-evidence-${index}`
                                                        }
                                                    >
                                                        <p className="evidence-source">
                                                            <strong>
                                                                Source {index + 1}
                                                            </strong>
                                                            {citation.source &&
                                                                ` · ${citation.source}`}
                                                            {citation.section &&
                                                                ` · ${citation.section}`}
                                                            {citation.page !==
                                                                null &&
                                                                citation.page !==
                                                                    undefined &&
                                                                ` · Page ${citation.page}`}
                                                        </p>
                                                        <blockquote className="citation-quote">
                                                            {citation.quote}
                                                        </blockquote>
                                                    </article>
                                                )
                                            )}
                                        </div>
                                    </section>
                                )}
                            </div>
                        )}
                        {citations.length === 0 && (
                            <section className="citation-empty-state">
                                <h3>Sources and evidence</h3>
                                <p>
                                    No citations were returned with this
                                    response.
                                </p>
                            </section>
                        )}
                    </article>
                </section>
                    )}
        </div>
    );
}

export default Chat;
