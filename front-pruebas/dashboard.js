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

// Función para convertir archivos en base64
function toBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);  // Devuelve solo la parte base64
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

// Función para determinar el endpoint basado en el tamaño del archivo
function getEndpointByFileSize(fileSize) {
    const MAX_SIZE_SINGLE = 350 * 1024 * 1024; // 350 MB en bytes
    if (fileSize > MAX_SIZE_SINGLE) {
        return 'chunk';  // Si el archivo es mayor a 350 MB, se envía al endpoint de chunks
    }
    return 'single';  // Si el archivo es menor o igual a 350 MB, se envía al endpoint estándar
}

// Subir un archivo con barra de progreso y decisión de endpoint
document.getElementById('submitUploadFile').addEventListener('click', async function () {
    const file = document.getElementById('singleFile').files[0];
    const filePath = document.getElementById('singleFilePath').value || '';

    if (!file) {
        document.getElementById('uploadFileMessage').innerText = 'Selecciona un archivo.';
        return;
    }

    const fileName = file.name;
    const fileSize = file.size;

    const endpointType = getEndpointByFileSize(fileSize);

    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    progressContainer.style.display = 'block';
    progressBar.value = 0;
    progressPercent.innerText = '0%';

    try {
        const token = localStorage.getItem('access_token');

        if (endpointType === 'single') {
            const fileBase64 = await toBase64(file);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', 'http://127.0.0.1:5000/file/upload/single', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);

            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    progressBar.value = percentComplete;
                    progressPercent.innerText = `${Math.round(percentComplete)}%`;
                }
            };

            xhr.onload = function () {
                const response = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    document.getElementById('uploadFileMessage').innerText = response.message || 'Archivo subido correctamente.';
                } else {
                    document.getElementById('uploadFileMessage').innerText = response.error || 'Error al subir el archivo.';
                }
                progressContainer.style.display = 'none';
            };

            const jsonData = JSON.stringify({
                file: fileBase64,
                filename: fileName,
                path: filePath
            });
            xhr.send(jsonData);

        } else if (endpointType === 'chunk') {
            // Enviar el archivo en chunks secuenciales
            const CHUNK_SIZE = 5 * 1024 * 1024;  // 5 MB por chunk
            const totalChunks = Math.ceil(fileSize / CHUNK_SIZE);

            for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
                const start = chunkIndex * CHUNK_SIZE;
                const end = Math.min(fileSize, start + CHUNK_SIZE);
                const chunk = file.slice(start, end);

                const chunkData = await chunk.arrayBuffer();

                const result = await sendChunk(chunkData, chunkIndex, totalChunks, fileName, filePath, token);

                if (!result.success) {
                    document.getElementById('uploadFileMessage').innerText = `Error al subir chunk ${chunkIndex + 1}: ${result.error}`;
                    progressContainer.style.display = 'none';
                    break;
                }

                // Actualizar barra de progreso
                const percentComplete = ((chunkIndex + 1) / totalChunks) * 100;
                progressBar.value = percentComplete;
                progressPercent.innerText = `${Math.round(percentComplete)}%`;
            }
        }

    } catch (error) {
        console.error('Error al subir el archivo:', error);
        document.getElementById('uploadFileMessage').innerText = 'Error al subir el archivo.';
    }
});

// Función para enviar un chunk al servidor
async function sendChunk(chunkData, chunkIndex, totalChunks, fileName, filePath, token) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://127.0.0.1:5000/file/upload/chunk', true);
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        xhr.setRequestHeader('X-Chunk-Index', chunkIndex);
        xhr.setRequestHeader('X-Total-Chunks', totalChunks);
        xhr.setRequestHeader('X-File-Name', fileName);
        xhr.setRequestHeader('X-File-Path', filePath);

        xhr.onload = function () {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                console.log(`Chunk ${chunkIndex + 1} subido con éxito`, response);
                resolve({ success: true });
            } else {
                const response = JSON.parse(xhr.responseText);
                console.error(`Error al subir chunk ${chunkIndex + 1}`, response);
                resolve({ success: false, error: response.error });
            }
        };

        xhr.onerror = function () {
            console.error(`Error al enviar chunk ${chunkIndex + 1}`);
            resolve({ success: false, error: 'Error de conexión con el servidor' });
        };

        // Enviar el chunk como binario
        xhr.send(chunkData);
    });
}

// Subir múltiples archivos con barra de progreso y decisión de endpoint
document.getElementById('submitUploadMultipleFiles').addEventListener('click', async function () {
    const files = document.getElementById('multipleFiles').files;
    const filePath = document.getElementById('multipleFilesPath').value || '';

    if (files.length === 0) {
        document.getElementById('uploadMultipleFilesMessage').innerText = 'Selecciona archivos.';
        return;
    }

    const progressContainer = document.getElementById('progressContainerMultiple');
    const progressBar = document.getElementById('progressBarMultiple');
    const progressPercent = document.getElementById('progressPercentMultiple');
    progressContainer.style.display = 'block';
    progressBar.value = 0;
    progressPercent.innerText = '0%';

    try {
        const token = localStorage.getItem('access_token');

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileName = file.name;
            const fileSize = file.size;

            // Decidir el endpoint según el tamaño del archivo
            const endpointType = getEndpointByFileSize(fileSize);

            if (endpointType === 'single') {
                // Convertir el archivo a base64
                const fileBase64 = await toBase64(file);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', 'http://127.0.0.1:5000/file/upload/lot', true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);

                // Progreso de carga
                xhr.upload.onprogress = function (event) {
                    if (event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        progressBar.value = percentComplete;
                        progressPercent.innerText = `${Math.round(percentComplete)}%`;
                    }
                };

                // Evento cuando la carga se completa
                xhr.onload = function () {
                    const response = JSON.parse(xhr.responseText);
                    if (xhr.status === 200) {
                        document.getElementById('uploadMultipleFilesMessage').innerText = response.message || 'Archivos subidos correctamente.';
                    } else {
                        document.getElementById('uploadMultipleFilesMessage').innerText = response.error || 'Error al subir los archivos.';
                    }
                    progressContainer.style.display = 'none';
                };

                // Enviar la solicitud con el archivo base64
                const jsonData = JSON.stringify({
                    files: [{ file: fileBase64, filename: fileName }],
                    path: filePath
                });
                xhr.send(jsonData);

            } else if (endpointType === 'chunk') {
                // Enviar el archivo en chunks si es mayor de 350 MB
                const CHUNK_SIZE = 5 * 1024 * 1024;  // 5 MB por chunk
                const totalChunks = Math.ceil(fileSize / CHUNK_SIZE);

                for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
                    const start = chunkIndex * CHUNK_SIZE;
                    const end = Math.min(fileSize, start + CHUNK_SIZE);
                    const chunk = file.slice(start, end);

                    const chunkData = await chunk.arrayBuffer();

                    const result = await sendChunk(chunkData, chunkIndex, totalChunks, fileName, filePath, token);

                    if (!result.success) {
                        document.getElementById('uploadMultipleFilesMessage').innerText = `Error al subir chunk ${chunkIndex + 1}: ${result.error}`;
                        progressContainer.style.display = 'none';
                        break;
                    }

                    // Actualizar barra de progreso
                    const percentComplete = ((chunkIndex + 1) / totalChunks) * 100;
                    progressBar.value = percentComplete;
                    progressPercent.innerText = `${Math.round(percentComplete)}%`;
                }
            }
        }

    } catch (error) {
        console.error('Error al subir los archivos:', error);
        document.getElementById('uploadMultipleFilesMessage').innerText = 'Error al subir los archivos.';
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



// Función para crear el árbol de archivos y carpetas recursivamente
function createFileTree(structure, container) {
    // Recorremos las claves del objeto de estructura (carpetas)
    for (const [folder, content] of Object.entries(structure)) {
        // Crear un contenedor para la carpeta o raíz
        const folderElement = document.createElement('div');
        folderElement.classList.add('folder'); // Clase para el estilo

        // Si el folder es la raíz (''), ponemos "Raíz del directorio"
        if (folder === '') {
            folderElement.textContent = 'Raíz del directorio';
        } else {
            folderElement.textContent = folder; // Nombre de la carpeta
        }

        // Crear un contenedor para el contenido de la carpeta
        const folderContent = document.createElement('div');
        folderContent.classList.add('folder-content');

        // Recorrer las subcarpetas
        if (content.folders.length > 0) {
            const subFolderList = document.createElement('ul');
            content.folders.forEach(subFolder => {
                const subFolderItem = document.createElement('li');
                subFolderItem.textContent = subFolder;
                subFolderList.appendChild(subFolderItem);
            });
            folderContent.appendChild(subFolderList);
        }

        // Recorrer los archivos
        if (content.files.length > 0) {
            const fileList = document.createElement('ul');
            content.files.forEach(file => {
                const fileItem = document.createElement('li');
                fileItem.textContent = file;
                fileList.appendChild(fileItem);
            });
            folderContent.appendChild(fileList);
        }

        // Colapsar el contenido de la carpeta al hacer clic
        folderElement.addEventListener('click', () => {
            folderContent.style.display =
                folderContent.style.display === 'none' ? 'block' : 'none';
        });

        // Por defecto, esconder el contenido de las carpetas
        folderContent.style.display = 'none';

        // Agregar la carpeta y su contenido al contenedor principal
        container.appendChild(folderElement);
        container.appendChild(folderContent);
    }
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
            createFileTree(data.structure, fileTreeContainer);
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
