document.getElementById('goToFilesButton').addEventListener('click', function () {
    window.location.href = 'files.html'; // Redirigir a files.html
});

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
    const forms = ['createUserForm', 'getUserForm', 'updateUserForm', 'deleteUserForm', 'uploadFileForm', 'uploadMultipleFilesForm', 'fileStructureContainer', 'downloadFileForm', 'downloadFolderForm'];
    forms.forEach(id => {
        const form = document.getElementById(id);
        if (form) {
            // Solo ocultar si no es el formulario que queremos mostrar
            form.style.display = (id === formId) ? 'block' : 'none';
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
    alert(JSON.stringify(dataToSend));
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

// Función para solicitar el contenido de un directorio específico
async function fetchDirectoryContent(path = '') {
    const token = localStorage.getItem('access_token');
    const dirPath = encodeURIComponent(path);  // Codificar la ruta en la URL

    try {
        const response = await fetch(`http://127.0.0.1:5000/file/list?dirPath=${dirPath}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`  // Agregar el token JWT
            },
        });

        const data = await response.json();

        if (response.ok) {
            const fileTreeContainer = document.getElementById('fileTree');
            createFileTree(data.structure, fileTreeContainer, path);  // Actualizar el árbol de archivos
        } else {
            document.getElementById('fileTree').innerText = data.error || 'Error al obtener la estructura de archivos.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('fileTree').innerText = 'Error en la conexión con la API.';
    }
}

// Mostrar la estructura de archivos al hacer clic en el botón de la raíz
document.getElementById('listFilesButton').addEventListener('click', async function () {
    await fetchDirectoryContent('');  // Llamada inicial para la raíz del directorio
});



// Mostrar la estructura de archivos al hacer clic en el botón de la raíz
document.getElementById('listFilesButton').addEventListener('click', async function () {
    await fetchDirectoryContent('');  // Llamada inicial para la raíz del directorio
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
            console.log(fileBase64);
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

// Función para crear el árbol de archivos y carpetas para un directorio específico
function createFileTree(structure, container, currentPath = '') {
    // Limpiar el contenedor actual antes de cargar el nuevo contenido
    container.innerHTML = '';

    // Mostrar carpetas
    if (structure.folders && structure.folders.length > 0) {
        const folderList = document.createElement('ul');

        structure.folders.forEach(folder => {
            const folderItem = document.createElement('li');
            
            // Crear contenedor para carpeta y botón
            const folderName = document.createElement('span');
            folderName.textContent = folder;
            folderName.style.cursor = 'pointer';

            // Evento para navegar a la carpeta al hacer clic en el nombre
            folderName.addEventListener('click', async function () {
                const newPath = currentPath ? `${currentPath}/${folder}` : folder;
                await fetchDirectoryContent(newPath);  // Solicitar el contenido de la nueva carpeta
            });

            // Crear botón de descarga para la carpeta
            const downloadButton = document.createElement('button');
            downloadButton.textContent = 'Descargar';
            downloadButton.style.marginLeft = '15px';

            // Evento del botón de descarga para la carpeta
            downloadButton.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation(); // Evitar que el clic en el botón expanda la carpeta

                // Asignar la ruta de la carpeta al campo del formulario de descarga
                document.getElementById('folderToDownload').value = currentPath ? `${currentPath}/${folder}` : folder;

                // Mostrar el formulario de descarga de la carpeta
                toggleForm('downloadFolderForm');
            });

            // Añadir el nombre de la carpeta y el botón al contenedor
            folderItem.appendChild(folderName);
            folderItem.appendChild(downloadButton);
            folderList.appendChild(folderItem);
        });

        container.appendChild(folderList);
    }

    // Mostrar archivos
    if (structure.files && structure.files.length > 0) {
        const fileList = document.createElement('ul');

        structure.files.forEach(file => {
            const fileItem = document.createElement('li');
            
            // Crear contenedor para archivo
            const fileName = document.createElement('span');
            fileName.textContent = file;

            // Crear botón de descarga para el archivo
            const downloadButton = document.createElement('button');
            downloadButton.textContent = 'Descargar';
            downloadButton.style.marginLeft = '15px';

            // Evento del botón de descarga para el archivo
            downloadButton.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation(); // Evitar que el clic en el botón active otras acciones

                // Asignar la ruta del archivo al campo del formulario de descarga
                document.getElementById('fileToDownload').value = currentPath ? `${currentPath}/${file}` : file;

                // Mostrar el formulario de descarga de archivos
                toggleForm('downloadFileForm');
            });

            // Añadir el nombre del archivo y el botón al contenedor
            fileItem.appendChild(fileName);
            fileItem.appendChild(downloadButton);
            fileList.appendChild(fileItem);
        });

        container.appendChild(fileList);
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

// Funcionalidad para descargar un archivo
document.getElementById('submitDownloadFile').addEventListener('click', async function () {
    const filePath = document.getElementById('fileToDownload').value;
    const token = localStorage.getItem('access_token');

    if (!filePath) {
        document.getElementById('downloadFileMessage').innerText = 'Por favor, ingresa la ruta del archivo.';
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/file/download?file_path=${encodeURIComponent(filePath)}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`  // Incluir el token JWT
            }
        });

        if (response.ok) {
            const blob = await response.blob();  // Convierte la respuesta en un blob para descargar
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filePath.split('/').pop();  // Asigna el nombre del archivo a descargar
            document.body.appendChild(a);
            a.click();  // Simula el clic para descargar el archivo
            a.remove();  // Elimina el enlace una vez descargado
            document.getElementById('downloadFileMessage').innerText = 'Archivo descargado correctamente.';
        } else {
            const errorData = await response.json();
            document.getElementById('downloadFileMessage').innerText = errorData.error || 'Error al descargar el archivo.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('downloadFileMessage').innerText = 'Error al descargar el archivo.';
    }
});

// Funcionalidad para descargar una carpeta como ZIP
document.getElementById('submitDownloadFolder').addEventListener('click', async function () {
    const folderPath = document.getElementById('folderToDownload').value;
    const token = localStorage.getItem('access_token');

    if (!folderPath) {
        document.getElementById('downloadFolderMessage').innerText = 'Por favor, ingresa la ruta de la carpeta.';
        return;
    }

    try {
        // Mostrar el spinner durante el procesamiento
        document.getElementById('loadingSpinner').style.display = 'block';

        const response = await fetch(`http://127.0.0.1:5000/file/download-folder?folder_path=${encodeURIComponent(folderPath)}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`  // Incluir el token JWT
            }
        });

        if (response.ok) {
            const blob = await response.blob();  // Convierte la respuesta en un blob para descargar
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${folderPath.split('/').pop()}.zip`;  // Nombre del archivo ZIP descargado
            document.body.appendChild(a);
            a.click();  // Simula el clic para descargar el archivo ZIP
            a.remove();  // Elimina el enlace una vez descargado
            document.getElementById('downloadFolderMessage').innerText = 'Carpeta descargada correctamente.';
        } else {
            const errorData = await response.json();
            document.getElementById('downloadFolderMessage').innerText = errorData.error || 'Error al descargar la carpeta.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('downloadFolderMessage').innerText = 'Error al descargar la carpeta.';
    } finally {
        // Ocultar el spinner cuando termine el proceso
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});
