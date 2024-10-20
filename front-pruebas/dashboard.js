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

document.getElementById('uploadFileButton').addEventListener('click', function () {
    toggleForm('uploadFileForm');
});

document.getElementById('uploadMultipleFilesButton').addEventListener('click', function () {
    toggleForm('uploadMultipleFilesForm');
});

document.getElementById('listFilesButton').addEventListener('click', function () {
    toggleForm('fileStructureContainer');
});

function toggleForm(formId) {
    const forms = ['createUserForm', 'getUserForm', 'updateUserForm', 'deleteUserForm', 'uploadFileForm', 'uploadMultipleFilesForm', 'fileStructureContainer'];
    forms.forEach(id => {
        const form = document.getElementById(id);
        if (form) {
            form.style.display = (id === formId) ? (form.style.display === 'none' ? 'block' : 'none') : 'none';
        }
    });
}

// Funcionalidad para verificar la autenticación
document.getElementById('checkAuthButton').addEventListener('click', async function () {
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch('http://127.0.0.1:5000/users/info', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
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
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch('http://127.0.0.1:5000/users/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
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
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
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
    const token = localStorage.getItem('access_token');

    const dataToSend = {
        ...(email && { email }),  // Solo incluir email si no es vacío
        ...(nombre && { nombre }),  // Solo incluir nombre si no es vacío
        ...(password && { password }),  // Solo incluir password si no es vacío
        ...(roleId && { role_id: roleId })  // Solo incluir role_id si no es vacío
    };

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
            },
            body: JSON.stringify(dataToSend),
        });

        const data = await response.json();
        document.getElementById('updateUserMessage').innerText = data.message || data.error;

        if (response.ok) {
            document.getElementById('updateUserForm').reset();  // Reiniciar formulario
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('updateUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para eliminar un usuario
document.getElementById('submitDeleteUser').addEventListener('click', async function () {
    const boleta = document.getElementById('deleteBoleta').value;
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`http://127.0.0.1:5000/users/${boleta}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
            },
        });

        const data = await response.json();
        document.getElementById('deleteUserMessage').innerText = data.message || data.error;

        if (response.ok) {
            document.getElementById('deleteUserForm').reset();  // Reiniciar formulario
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
    const token = localStorage.getItem('access_token');

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
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
            },
            body: JSON.stringify(dataToSend),
        });

        const data = await response.json();
        document.getElementById('createUserMessage').innerText = data.message || data.error;

        if (response.ok) {
            document.getElementById('createUserForm').reset();  // Reiniciar formulario
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('createUserMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Funcionalidad para cerrar sesión
document.getElementById('logoutButton').addEventListener('click', async function () {
    try {
        localStorage.removeItem('access_token');
        window.location.href = 'index.html';  // Redirigir a la página de inicio de sesión
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('authMessage').innerText = 'Error en la conexión con la API.';
    }
});

// Función para generar el árbol de carpetas y archivos
function createFileTree(structure, parentElement) {
    const ul = document.createElement('ul');

    for (const key in structure) {
        const li = document.createElement('li');

        if (typeof structure[key] === 'object') {
            // Si es una carpeta
            li.innerHTML = `<strong>${key}/</strong>`;
            const subUl = createFileTree(structure[key], li);
            li.appendChild(subUl);
        } else {
            // Si es un archivo
            li.innerHTML = `${key}`;
        }

        ul.appendChild(li);
    }

    return ul;
}

// Mostrar la estructura de archivos al hacer clic en el botón
document.getElementById('listFilesButton').addEventListener('click', async function () {
    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch('http://127.0.0.1:5000/file/list', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT al encabezado
            },
        });

        const data = await response.json();

        if (response.ok) {
            // Limpiar el contenedor anterior
            const fileTreeContainer = document.getElementById('fileTree');
            fileTreeContainer.innerHTML = '';

            // Crear el árbol de archivos y carpetas
            const fileTree = createFileTree(data.structure, fileTreeContainer);
            fileTreeContainer.appendChild(fileTree);
            document.getElementById('fileStructureContainer').style.display = 'block';
        } else {
            document.getElementById('fileTree').innerText = data.error || 'Error al obtener la estructura de archivos.';
            document.getElementById('fileStructureContainer').style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('fileTree').innerText = 'Error en la conexión con la API.';
        document.getElementById('fileStructureContainer').style.display = 'block';
    }
});
