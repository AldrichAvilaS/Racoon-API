// Mostrar y ocultar formularios según el botón clicado
document.getElementById('createUserButton').addEventListener('click', function () {
    toggleForm('createUserForm');
});

document.getElementById('getUserButton').addEventListener('click', function () {
    toggleForm('getUserForm');
});

document.getElementById('updateUserButton').addEventListener('click', function () {
    toggleForm('updateUserForm');
});

document.getElementById('deleteUserButton').addEventListener('click', function () {
    toggleForm('deleteUserForm');
});

function toggleForm(formId) {
    const forms = ['createUserForm', 'getUserForm', 'updateUserForm', 'deleteUserForm'];
    forms.forEach(id => {
        const form = document.getElementById(id);
        if (form) { // Asegúrate de que el formulario exista
            form.style.display = (id === formId) ? (form.style.display === 'none' ? 'block' : 'none') : 'none';
        }
    });
}

// Funcionalidad para verificar la autenticación
document.getElementById('checkAuthButton').addEventListener('click', async function () {
    try {
        const response = await fetch('http://127.0.0.1:5000/users/info', {
            method: 'GET',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        document.getElementById('authMessage').innerText = response.ok ? 
            `Usuario autenticado: ${JSON.stringify(data)}` : data.error;
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('authMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para obtener todos los usuarios
document.getElementById('getUsersButton').addEventListener('click', async function () {
    try {
        const response = await fetch('http://127.0.0.1:5000/users/', {
            method: 'GET',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        document.getElementById('responseMessage').innerText = JSON.stringify(data);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('responseMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para obtener un usuario por boleta
document.getElementById('submitGetUser').addEventListener('click', async function () {
    const boleta = document.getElementById('userBoleta').value;

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'GET',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        document.getElementById('getUserMessage').innerText = data.error || JSON.stringify(data);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('getUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para actualizar un usuario
document.getElementById('submitUpdateUser').addEventListener('click', async function () {
    const boleta = document.getElementById('updateBoleta').value;
    const email = document.getElementById('updateEmail').value;
    const nombre = document.getElementById('updateNombre').value;
    const password = document.getElementById('updatePassword').value;
    const roleId = document.getElementById('updateRoleId').value;

    // Crear el objeto de datos a enviar
    const dataToSend = {
        ...(email && { email }),  // Solo incluir email si no es vacío
        ...(nombre && { nombre }),  // Solo incluir nombre si no es vacío
        ...(password && { password }),  // Solo incluir password si no es vacío
        ...(roleId && { role_id: roleId })  // Solo incluir role_id si no es vacío
    };

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'PUT',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSend),
        });

        const data = await response.json();
        document.getElementById('updateUserMessage').innerText = data.message || data.error;

        // Reiniciar formulario solo si la operación fue exitosa
        if (response.ok) {
            document.getElementById('updateUserForm').reset(); // Reiniciar formulario
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('updateUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para eliminar un usuario
document.getElementById('submitDeleteUser').addEventListener('click', async function () {
    const boleta = document.getElementById('deleteBoleta').value;

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'DELETE',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        document.getElementById('deleteUserMessage').innerText = data.message || data.error;

        // Reiniciar formulario solo si la operación fue exitosa
        if (response.ok) {
            document.getElementById('deleteUserForm').reset(); // Reiniciar formulario
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('deleteUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para crear un nuevo usuario
document.getElementById('submitCreateUser').addEventListener('click', async function () {
    const boleta = document.getElementById('newBoleta').value;
    const email = document.getElementById('newEmail').value;
    const password = document.getElementById('newPassword').value;
    const nombre = document.getElementById('newNombre').value;
    const roleId = document.getElementById('newRoleId').value || null;

    const dataToSend = {
        boleta,
        email,
        password,
        nombre,
        role_id: roleId
    };

    try {
        const response = await fetch('http://127.0.0.1:5000/users/', {
            method: 'POST',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSend),
        });

        const data = await response.json();
        document.getElementById('createUserMessage').innerText = data.message || data.error;

        // Reiniciar formulario solo si la operación fue exitosa
        if (response.ok) {
            document.getElementById('createUserForm').reset(); // Reiniciar formulario
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('createUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para cerrar sesión
document.getElementById('logoutButton').addEventListener('click', async function () {
    try {
        const response = await fetch('http://127.0.0.1:5000/auth/logout', {
            method: 'POST',
            credentials: 'include',  // Incluye las cookies de sesión
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();
        document.getElementById('authMessage').innerText = data.message || data.error;
        window.location.href = 'index.html'; // Redirige a la página de inicio de sesión
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('authMessage').innerText = 'Error en la conexión con la API.';
    }
});