import { useMemo, useState } from "react";
import { login as requestLogin } from "../api/lexintel";
import { AuthContext } from "./context";
const SESSION_KEY = "lexintel.auth";

function readSession() {
    try {
        const stored = sessionStorage.getItem(SESSION_KEY);
        if (!stored) {
            return null;
        }
        const session = JSON.parse(stored);
        if (
            typeof session.accessToken !== "string" ||
            !Number.isFinite(session.expiresAt) ||
            session.expiresAt <= Date.now()
        ) {
            sessionStorage.removeItem(SESSION_KEY);
            return null;
        }
        return session;
    } catch {
        sessionStorage.removeItem(SESSION_KEY);
        return null;
    }
}

export function AuthProvider({ children }) {
    const [session, setSession] = useState(readSession);

    async function signIn(usernameOrEmail, password) {
        const result = await requestLogin(usernameOrEmail, password);
        const nextSession = {
            accessToken: result.access_token,
            expiresAt: Date.now() + result.expires_in * 1000,
            user: result.user,
        };
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
        setSession(nextSession);
    }

    function signOut() {
        sessionStorage.removeItem(SESSION_KEY);
        setSession(null);
    }

    const value = useMemo(
        () => ({
            accessToken: session?.accessToken ?? null,
            user: session?.user ?? null,
            isAuthenticated: Boolean(session?.accessToken),
            login: signIn,
            logout: signOut,
        }),
        [session]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
