const API_URL = 'http://localhost:8000/api';

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        // Call Django JWT token endpoint
        const response = await fetch(`${API_URL}/token/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) throw new Error('Invalid credentials');
        
        const data = await response.json();
        localStorage.setItem('token', data.access); // Save JWT token
        
        // Redirect to dashboard
        window.location.href = 'dashboard.html';
    } catch (error) {
        document.getElementById('error').textContent = 'Login failed!';
    }
});

// Check if logged in (for other pages)
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) window.location.href = 'index.html';
    return token;
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}