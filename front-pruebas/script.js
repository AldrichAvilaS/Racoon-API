document.getElementById('loginForm').addEventListener('submit', async function (event) {
    event.preventDefault();

    const boleta = document.getElementById('boleta').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // Incluye las credenciales para permitir las cookies
            body: JSON.stringify({ boleta, password }),
        });

        const data = await response.json();

        if (response.ok) {
            // Redirigir a la página del dashboard
            window.location.href = 'dashboard.html';
        } else {
            document.getElementById('message').innerText = data.message || data.error;
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').innerText = 'Error en la conexión con la API.';
    }
});
