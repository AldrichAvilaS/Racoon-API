// URL base de la API
const API_BASE_URL = 'http://localhost:5000';

// Variables globales
let accessToken = null;
let userType = null;

// Función para mostrar mensajes en el área de respuesta
function showResponse(message) {
    document.getElementById('server-response').textContent = JSON.stringify(message, null, 2);
}

// Manejo del inicio de sesión
document.getElementById('login-button').addEventListener('click', async () => {
    const identifier = document.getElementById('identifier').value;
    const password = document.getElementById('password').value;

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password })
    });

    const data = await response.json();
    showResponse(data);

    if (response.ok) {
        accessToken = data.access_token;
        userType = data.user_type;
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('session-info').style.display = 'block';
        document.getElementById('user-type').textContent = userType;
        document.getElementById('file-section').style.display = 'block';

        if (userType === 'Administrador' || userType === 'Academia') {
            document.getElementById('admin-section').style.display = 'block';
        }
    } else {
        alert('Error al iniciar sesión: ' + data.error);
    }
});

// Manejo del cierre de sesión
document.getElementById('logout-button').addEventListener('click', () => {
    accessToken = null;
    userType = null;
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('session-info').style.display = 'none';
    document.getElementById('file-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
    showResponse({});
});

// Manejo de la subida de archivos
document.getElementById('upload-button').addEventListener('click', async () => {
    const fileInput = document.getElementById('file-input');
    const path = document.getElementById('upload-path').value || '';
    if (fileInput.files.length === 0) {
        alert('Selecciona un archivo para subir.');
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = async function(event) {
        const fileData = btoa(event.target.result);
        const response = await fetch(`${API_BASE_URL}/file/upload/single`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + accessToken
            },
            body: JSON.stringify({
                file: fileData,
                filename: file.name,
                path: path
            })
        });

        const data = await response.json();
        showResponse(data);

        if (!response.ok) {
            alert('Error al subir el archivo: ' + data.error);
        }
    };
    reader.readAsBinaryString(file);
});

// Manejo de la lista de archivos
document.getElementById('list-button').addEventListener('click', async () => {
    const dirPath = document.getElementById('list-path').value || '';
    const response = await fetch(`${API_BASE_URL}/file/list?dirPath=${encodeURIComponent(dirPath)}`, {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer ' + accessToken
        }
    });

    const data = await response.json();
    showResponse(data);

    if (response.ok) {
        const fileListDiv = document.getElementById('file-list');
        fileListDiv.innerHTML = '';
        const structure = data.structure;

        const ulFolders = document.createElement('ul');
        ulFolders.innerHTML = '<strong>Carpetas:</strong>';
        structure.folders.forEach(folder => {
            const li = document.createElement('li');
            li.textContent = folder;
            ulFolders.appendChild(li);
        });

        const ulFiles = document.createElement('ul');
        ulFiles.innerHTML = '<strong>Archivos:</strong>';
        structure.files.forEach(file => {
            const li = document.createElement('li');
            li.textContent = file;
            ulFiles.appendChild(li);
        });

        fileListDiv.appendChild(ulFolders);
        fileListDiv.appendChild(ulFiles);
    } else {
        alert('Error al listar archivos: ' + data.error);
    }
});

// Aquí puedes añadir más funciones para otras operaciones como crear carpetas, mover archivos, gestionar usuarios, etc.
