import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

function Login() {
    const { login } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();
        setErrorMessage("");
        setIsSubmitting(true);
        try {
            await login(identifier, password);
            navigate(location.state?.from?.pathname || "/", { replace: true });
        } catch (error) {
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to sign in. Please try again."
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main id="main-content" className="page-shell login-page">
            <section className="card login-card" aria-labelledby="login-title">
                <p className="eyebrow">Legal intelligence workspace</p>
                <h1 id="login-title">Welcome to LexIntel AI</h1>
                <p className="page-intro">
                    Sign in to continue to your legal research workspace.
                </p>
                <form className="login-form" onSubmit={handleSubmit}>
                    <label htmlFor="login-identifier">Email or username</label>
                    <input
                        id="login-identifier"
                        name="username_or_email"
                        type="text"
                        autoComplete="username"
                        required
                        value={identifier}
                        onChange={(event) => setIdentifier(event.target.value)}
                    />
                    <label htmlFor="login-password">Password</label>
                    <input
                        id="login-password"
                        name="password"
                        type="password"
                        autoComplete="current-password"
                        required
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                    />
                    {errorMessage && (
                        <p className="status-message status-error" role="alert">
                            {errorMessage}
                        </p>
                    )}
                    <button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "Signing in…" : "Sign in"}
                    </button>
                    <p className="account-prompt">
                        Don&apos;t have an account?{" "}
                        <Link to="/register">Create Account</Link>
                    </p>
                </form>
            </section>
        </main>
    );
}

export default Login;
