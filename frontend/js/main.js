// Base API Endpoint Configuration
const API_BASE_URL = "http://127.0.0.1:8000/api";

/**
 * Retrieve active JWT Token from localStorage
 */
function getAuthToken() {
    return localStorage.getItem("token") || "";
}

/**
 * Enforce Authentication Check across protected pages
 */
function requireAuth() {
    const token = getAuthToken();
    const currentPath = window.location.pathname;
    
    // Check if the current page is an authentication page
    const isAuthPage = currentPath.includes("login.html") || currentPath.includes("register.html");

    if (!token && !isAuthPage) {
        // Redirect to login page using relative pathing
        window.location.href = "../pages/login.html";
    }
}

/**
 * Global API Fetch Wrapper (Applies Authorization Headers automatically)
 */
async function authFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        ...(token ? { "Authorization": `Bearer ${token}` } : {})
    };

    const response = await fetch(url, { ...options, headers });
    
    // Automatically redirect to login if session expires or token is invalid
    if (response.status === 401) {
        logout();
        throw new Error("Session expired. Please log in again.");
    }

    return response;
}

/**
 * Dynamically configure Navbar display based on session state
 */
function setupNavbar() {
    const navRight = document.getElementById("nav-right");
    if (!navRight) return;

    const token = getAuthToken();
    const userName = localStorage.getItem("user_name") || "User";

    if (token) {
        navRight.innerHTML = `
            <span style="margin-right: 1rem; color: #475569; font-weight: 600;">Hi, ${userName}</span>
            <button onclick="logout()" class="btn" style="background: #ef4444; padding: 0.4rem 0.8rem; font-size: 0.85rem; cursor: pointer;">Logout</button>
        `;
    } else {
        navRight.innerHTML = `
            <a href="../pages/login.html" class="btn" style="padding: 0.4rem 0.8rem; font-size: 0.85rem; text-decoration: none;">Login</a>
        `;
    }
}

/**
 * Clear user auth session and redirect to Login screen
 */
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_role");
    window.location.href = "../pages/login.html";
}

// Automatically bind setup logic on DOM Content Ready
document.addEventListener("DOMContentLoaded", () => {
    setupNavbar();
});