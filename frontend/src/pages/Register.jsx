import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerUser } from "../api/lexintel";

const initialValues = {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
};

function validate(values) {
    const errors = {};

    if (!values.username.trim()) {
        errors.username = "Username is required.";
    }
    if (!values.email.trim()) {
        errors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) {
        errors.email = "Enter a valid email address.";
    }
    if (!values.password) {
        errors.password = "Password is required.";
    }
    if (!values.confirmPassword) {
        errors.confirmPassword = "Confirm Password is required.";
    } else if (values.password !== values.confirmPassword) {
        errors.confirmPassword = "Passwords do not match.";
    }

    return errors;
}

function Register() {
    const navigate = useNavigate();
    const [values, setValues] = useState(initialValues);
    const [fieldErrors, setFieldErrors] = useState({});
    const [errorMessage, setErrorMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isRegistered, setIsRegistered] = useState(false);

    useEffect(() => {
        if (!isRegistered) {
            return undefined;
        }
        const redirectTimer = window.setTimeout(
            () => navigate("/login", { replace: true }),
            2000
        );
        return () => window.clearTimeout(redirectTimer);
    }, [isRegistered, navigate]);

    function handleChange(event) {
        const { name, value } = event.target;
        setValues((currentValues) => ({ ...currentValues, [name]: value }));
        setFieldErrors((currentErrors) => ({ ...currentErrors, [name]: "" }));
        setErrorMessage("");
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setErrorMessage("");
        const errors = validate(values);
        setFieldErrors(errors);
        if (Object.keys(errors).length > 0) {
            return;
        }

        setIsSubmitting(true);
        try {
            await registerUser(
                values.username.trim(),
                values.email.trim(),
                values.password
            );
            setIsRegistered(true);
        } catch (error) {
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to create the account."
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main id="main-content" className="page-shell login-page">
            <section className="card login-card" aria-labelledby="register-title">
                <p className="eyebrow">Legal intelligence workspace</p>
                <h1 id="register-title">Create your account</h1>
                <p className="page-intro">
                    Register to start using your legal research workspace.
                </p>
                <form
                    className="login-form"
                    onSubmit={handleSubmit}
                    noValidate
                >
                    <label htmlFor="register-username">Username</label>
                    <input
                        id="register-username"
                        name="username"
                        type="text"
                        autoComplete="username"
                        required
                        value={values.username}
                        onChange={handleChange}
                        aria-invalid={Boolean(fieldErrors.username)}
                        aria-describedby={
                            fieldErrors.username
                                ? "register-username-error"
                                : undefined
                        }
                    />
                    {fieldErrors.username && (
                        <p
                            className="status-message status-error field-error"
                            id="register-username-error"
                        >
                            {fieldErrors.username}
                        </p>
                    )}

                    <label htmlFor="register-email">Email</label>
                    <input
                        id="register-email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        value={values.email}
                        onChange={handleChange}
                        aria-invalid={Boolean(fieldErrors.email)}
                        aria-describedby={
                            fieldErrors.email ? "register-email-error" : undefined
                        }
                    />
                    {fieldErrors.email && (
                        <p
                            className="status-message status-error field-error"
                            id="register-email-error"
                        >
                            {fieldErrors.email}
                        </p>
                    )}

                    <label htmlFor="register-password">Password</label>
                    <input
                        id="register-password"
                        name="password"
                        type="password"
                        autoComplete="new-password"
                        required
                        value={values.password}
                        onChange={handleChange}
                        aria-invalid={Boolean(fieldErrors.password)}
                        aria-describedby={
                            fieldErrors.password
                                ? "register-password-error"
                                : undefined
                        }
                    />
                    {fieldErrors.password && (
                        <p
                            className="status-message status-error field-error"
                            id="register-password-error"
                        >
                            {fieldErrors.password}
                        </p>
                    )}

                    <label htmlFor="register-confirm-password">
                        Confirm Password
                    </label>
                    <input
                        id="register-confirm-password"
                        name="confirmPassword"
                        type="password"
                        autoComplete="new-password"
                        required
                        value={values.confirmPassword}
                        onChange={handleChange}
                        aria-invalid={Boolean(fieldErrors.confirmPassword)}
                        aria-describedby={
                            fieldErrors.confirmPassword
                                ? "register-confirm-password-error"
                                : undefined
                        }
                    />
                    {fieldErrors.confirmPassword && (
                        <p
                            className="status-message status-error field-error"
                            id="register-confirm-password-error"
                        >
                            {fieldErrors.confirmPassword}
                        </p>
                    )}

                    {errorMessage && (
                        <p className="status-message status-error" role="alert">
                            {errorMessage}
                        </p>
                    )}
                    {isRegistered && (
                        <p className="status-message status-success" role="status">
                            Account created successfully. Redirecting to login…
                        </p>
                    )}
                    <button
                        type="submit"
                        disabled={isSubmitting || isRegistered}
                    >
                        {isSubmitting ? "Creating account…" : "Create Account"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default Register;
