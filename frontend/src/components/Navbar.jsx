import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

function Navbar() {
    const { isAuthenticated, logout, user } = useAuth();

    if (!isAuthenticated) {
        return null;
    }

    return (
        <header className="app-navbar">
            <Link className="brand-mark" to="/" aria-label="LexIntel AI dashboard">
                LI
            </Link>
            <nav className="primary-navigation" aria-label="Primary navigation">
                <NavLink to="/" end>Dashboard</NavLink>
                <NavLink to="/upload">Upload Document</NavLink>
                <NavLink to="/documents">Document History</NavLink>
                <NavLink to="/ask">Ask AI</NavLink>
                <NavLink to="/evaluation-metrics">Evaluation Metrics</NavLink>
            </nav>
            <div className="navbar-account">
                {user?.username && <span>{user.username}</span>}
                <button className="logout-button" type="button" onClick={logout}>
                    Log out
                </button>
            </div>
        </header>
    );
}

export default Navbar;
