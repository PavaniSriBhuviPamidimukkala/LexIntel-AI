import { useState } from "react";
import { askQuestion } from "../api/lexintel";
import Citation from "./Citation";


function Chat() {

    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [citations, setCitations] = useState([]);
    const [loading, setLoading] = useState(false);


    async function handleAsk() {

        if (!question.trim()) {
            alert("Enter a question");
            return;
        }


        try {

            setLoading(true);

            const result = await askQuestion(question);


            setAnswer(result.answer);

            setCitations(
                result.citations || []
            );


        } catch(error) {

            setAnswer(
                "Unable to get response"
            );

        } finally {

            setLoading(false);

        }
    }


    return (
        <div>

            <h2>
                Ask Legal Question
            </h2>


            <textarea
                rows="4"
                placeholder="Ask something about your uploaded document..."
                value={question}
                onChange={
                    e => setQuestion(e.target.value)
                }
            />


            <br />


            <button
                onClick={handleAsk}
                disabled={loading}
            >
                {
                    loading
                    ? "Searching..."
                    : "Ask"
                }
            </button>



            {
                answer &&
                <div>

                    <h3>
                        Answer
                    </h3>


                    <p>
                        {answer}
                    </p>


                    <h3>
                        Sources
                    </h3>


                    {
                        citations.map(
                            (item,index)=>(
                                <Citation
                                    key={index}
                                    data={item}
                                />
                            )
                        )
                    }

                </div>
            }


        </div>
    );
}


export default Chat;