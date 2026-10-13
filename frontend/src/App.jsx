import { lazy, Suspense } from "react";
import {
    BrowserRouter,
    Navigate,
    Route,
    Routes,
} from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/useAuth";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Ask from "./pages/Ask";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Upload from "./pages/Upload";
import "./App.css";

const EvaluationMetrics = lazy(() => import("./pages/EvaluationMetrics"));
const AccessibilityPage = lazy(() =>
    import("./pages/EvaluationMetrics").then((page) => ({
        default: page.AccessibilityPage,
    }))
);

function LoginRoute() {
    const { isAuthenticated } = useAuth();
    return isAuthenticated ? <Navigate to="/" replace /> : <Login />;
}

function AppRoutes() {
    return (
        <div className="app-container">
            <a className="skip-link" href="#main-content">
                Skip to main content
            </a>
            <Navbar />
            <Suspense
                fallback={
                    <main id="main-content" className="page-shell">
                        <p role="status" aria-live="polite">
                            Loading page…
                        </p>
                    </main>
                }
            >
                <Routes>
                    <Route path="/login" element={<LoginRoute />} />
                    <Route path="/register" element={<Register />} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/upload" element={<Upload />} />
                        <Route path="/documents" element={<Documents />} />
                        <Route path="/ask" element={<Ask />} />
                        <Route
                            path="/evaluation-metrics"
                            element={<EvaluationMetrics />}
                        />
                        <Route
                            path="/evaluation-metrics/accessibility"
                            element={<AccessibilityPage />}
                        />
                    </Route>
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </Suspense>
        </div>
    );
}

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;
