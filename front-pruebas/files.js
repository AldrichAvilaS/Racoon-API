document.addEventListener('DOMContentLoaded', function () {
    const gridContainer = document.getElementById('gridContainer');
    const downloadButton = document.getElementById('downloadButton');
    const deleteButton = document.getElementById('deleteButton');
    const moveButton = document.getElementById('moveButton');
    const backButton = document.getElementById('backButton');
    const newFolder = document.getElementById('newFolder');
    const downloadCurrentFolderButton = document.getElementById('downloadCurrentFolderButton');
    const deleteCurrentFolderButton = document.getElementById('deleteCurrentFolderButton');
    let selectedItem = null;
    let currentPath = '';
    let itemToMove = null;
    let isSelectingDestination = false;
    // Elemento para mostrar el estado de descarga
    const downloadStatus = document.createElement('div');
    downloadStatus.id = 'downloadStatus';
    downloadStatus.style.display = 'none';  // Ocultarlo inicialmente
    downloadStatus.style.marginTop = '10px';
    document.body.appendChild(downloadStatus);

    // Función para mostrar el estado de la descarga
    function showDownloadStatus(message) {
        downloadStatus.textContent = message;
        downloadStatus.style.display = 'block';
    }

    // Función para ocultar el estado de la descarga
    function hideDownloadStatus() {
        downloadStatus.style.display = 'none';
    }

    // Función para solicitar el contenido de un directorio específico
    async function fetchDirectoryContent(path = '') {
        const token = localStorage.getItem('access_token');
        const dirPath = encodeURIComponent(path);  // Codificar la ruta en la URL
        try {
            const response = await fetch('http://127.0.0.1:5000/file/list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`  // Agregar el token JWT
                },
                body: JSON.stringify({ dirPath: path })  // Enviar la ruta en el cuerpo de la solicitud
            });

            const data = await response.json();

            if (response.ok) {
                displayGridItems(data.structure, path);  // Mostrar archivos y carpetas en la cuadrícula
            } else {
                alert(data.error || 'Error al obtener la estructura de archivos.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error en la conexión con la API.');
        }
    }

    // Función para mostrar los ítems en la cuadrícula
    function displayGridItems(structure, path) {
        currentPath = path; // Actualizar la ruta actual
        gridContainer.innerHTML = ''; // Limpiar la cuadrícula

        // Mostrar el botón "Regresar a la carpeta anterior" si no estamos en la raíz
        if (currentPath && currentPath !== '') {
            const backFolderItem = document.createElement('div');
            backFolderItem.classList.add('grid-item', 'back-folder-item');  // Agregar una clase para el estilo
            backFolderItem.textContent = '⬅ Regresar a la carpeta anterior';
            backFolderItem.style.backgroundColor = '#ffcccc';  // Color distinto para "Regresar"
            backFolderItem.style.cursor = 'pointer';

            backFolderItem.addEventListener('click', function () {
                if (currentPath.includes('/')) {
                    const parentPath = currentPath.split('/').slice(0, -1).join('/');
                    fetchDirectoryContent(parentPath);
                } else {
                    fetchDirectoryContent('');
                }
            });

            gridContainer.appendChild(backFolderItem);  // Añadir el botón a la cuadrícula
        }

        // Mostrar carpetas
        if (structure.folders && structure.folders.length > 0) {
            structure.folders.forEach(folder => {
                const folderItem = document.createElement('div');
                folderItem.classList.add('grid-item');
                folderItem.textContent = folder;
                folderItem.style.backgroundColor = '#cceeff';  // Color para carpetas
                folderItem.dataset.type = 'folder';

                folderItem.addEventListener('click', () => handleFolderClick(folder));

                gridContainer.appendChild(folderItem);
            });
        }

        // Mostrar archivos

        if (structure.files && structure.files.length > 0) {
            structure.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.classList.add('grid-item');

                // Crear una estructura de visualización para el archivo con fecha, nombre, y tamaño
                fileItem.innerHTML = `
            <strong>${file.path}</strong><br>
            Fecha: ${file.date}<br>
            Tamaño: ${file.size} MB
        `;
                fileItem.style.backgroundColor = '#e6e6e6';  // Color para archivos
                fileItem.dataset.type = 'file';
                fileItem.dataset.name = file.path;
                fileItem.addEventListener('click', () => handleSelection(file.path));

                gridContainer.appendChild(fileItem);
            });
        }

        // Mostrar el botón "Descargar carpeta actual"
        downloadCurrentFolderButton.style.display = 'block';
    }

    // Función para manejar la selección de un archivo o carpeta
    function handleSelection(name) {
        // Desactivar la selección previa
        if (selectedItem) {
            selectedItem.style.backgroundColor = '#fff';
        }

        // Buscar el elemento seleccionado en la cuadrícula
        const items = Array.from(gridContainer.children);
        selectedItem = items.find(item => item.textContent.includes(name));
        if (selectedItem) {
            selectedItem.style.backgroundColor = '#d0e1ff';
        }

        // Habilitar botones
        downloadButton.disabled = false;
        deleteButton.disabled = false;
        moveButton.disabled = false;

        // Actualizar los textos de los botones
        downloadButton.textContent = `Descargar ${name}`;
        deleteButton.textContent = `Eliminar ${name}`;
        moveButton.textContent = `Mover ${name}`;
    }


    // Modifica la función de selección de carpetas para manejar el destino de movimiento
    function handleFolderClick(folder) {
        const newPath = currentPath ? `${currentPath}/${folder}` : folder;

        if (isSelectingDestination && itemToMove) {
            moveItem(itemToMove, newPath); // Llama a la función para mover el elemento
            isSelectingDestination = false; // Desactiva el modo de selección de destino
            itemToMove = null; // Resetea el archivo o carpeta a mover
        } else {
            fetchDirectoryContent(newPath); // Si no estamos en modo de selección, navega a la carpeta
        }
    }


    // Función para crear una nueva carpeta
    newFolder.addEventListener('click', function () {
        const folderName = prompt('Nombre de la nueva carpeta:');  // Solicitar el nombre de la nueva carpeta

        if (folderName) {
            createFolder(folderName, currentPath);  // Llamar a la función para crear la carpeta
        }
    });

    // Función para crear una carpeta en el servidor
    async function createFolder(folderName, parentDir = '') {
        const token = localStorage.getItem('access_token');
        const data = {
            folder_name: folderName,
            parent_dir: parentDir
        };

        try {
            const response = await fetch('http://127.0.0.1:5000/file/create-folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                console.log(result.message);
                fetchDirectoryContent(currentPath);  // Recargar el contenido actual del directorio
            } else {
                console.error(result.error);
                alert(result.error || 'Error al crear la carpeta.');
            }
        } catch (error) {
            console.error('Error al crear la carpeta:', error);
        }
    }

    // Función para descargar la carpeta actual como ZIP
    downloadCurrentFolderButton.addEventListener('click', async function () {
        downloadCurrentFolderButton.disabled = true;  // Deshabilitar el botón
        showDownloadStatus('Procesando la descarga de la carpeta...');  // Mostrar mensaje
        await downloadFolder(currentPath);
        hideDownloadStatus();
        downloadCurrentFolderButton.disabled = false;  // Habilitar el botón de nuevo
    });

    // Función para eliminar la carpeta actual 
    deleteCurrentFolderButton.addEventListener('click', async function () {
        deleteCurrentFolderButton.disabled = true;  // Deshabilitar el botón
        showDownloadStatus('Procesando la eliminación de la carpeta...');  // Mostrar mensaje
        await deletepath(currentPath);
        hideDownloadStatus();
        deleteCurrentFolderButton.disabled = false;  // Habilitar el botón de nuevo
    });

    // Función para mover un archivo o carpeta
    moveButton.addEventListener('click', function () {
        if (selectedItem) {
            itemToMove = selectedItem.dataset.name; // Almacena el archivo o carpeta a mover
            isSelectingDestination = true; // Habilita el modo de selección de destino
            alert("Selecciona la carpeta de destino para mover el elemento seleccionado.");
        } else {
            alert("Selecciona un archivo o carpeta para mover.");
        }
    });

// Función para mover un archivo o carpeta
async function moveItem(itemPath, destinationPath) {
    const token = localStorage.getItem('access_token');
    const data = {
        source_path: currentPath ? `${currentPath}/${itemPath}` : itemPath,
        destination_path: destinationPath
    };

    try {
        const response = await fetch('http://127.0.0.1:5000/file/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message || 'Elemento movido exitosamente.');
            fetchDirectoryContent(currentPath); // Recargar el contenido actual del directorio
        } else {
            console.error(result.error);
            alert(result.error || 'Error al mover el archivo o carpeta.');
        }
    } catch (error) {
        console.error('Error al mover el archivo o carpeta:', error);
    }
}



    // Función para eliminar la carpeta actual
    async function deletepath(folderPath) {
        const token = localStorage.getItem('access_token');
        const data = {
            target_path: folderPath
        };

        try {
            const response = await fetch('http://127.0.0.1:5000/file/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`  // Incluir el token JWT
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                console.log(result.message);
                fetchDirectoryContent('');  // Recargar el contenido actual del directorio
            } else {
                console.error(result.error);
                alert(result.error || 'Error al eliminar la carpeta.');
            }
        } catch (error) {
            console.error('Error al eliminar la carpeta:', error);
        }
    }

    // Función para manejar la descarga del archivo o carpeta seleccionada
    downloadButton.addEventListener('click', async function () {
        if (selectedItem) {
            const itemName = selectedItem.dataset.name;
            const itemType = selectedItem.dataset.type;
            const fullPath = currentPath ? `${currentPath}/${itemName}` : itemName;

            showDownloadStatus(`Descargando ${itemName}...`);  // Mostrar mensaje de descarga
            if (itemType === 'file') {
                await downloadFile(fullPath);
            } else if (itemType === 'folder') {
                await downloadFolder(fullPath);
            }
            hideDownloadStatus();  // Ocultar mensaje de descarga una vez que se complete
        }
    });

    // Función para manejar la descarga del archivo o carpeta seleccionada
    deleteButton.addEventListener('click', async function () {
        if (selectedItem) {
            const itemName = selectedItem.dataset.name;
            const itemType = selectedItem.dataset.type;
            const fullPath = currentPath ? `${currentPath}/${itemName}` : itemName;

            showDownloadStatus(`Descargando ${itemName}...`);  // Mostrar mensaje de descarga
            await deleteItem(fullPath, itemType);
        }
    });
    // Función para eliminar un archivo o carpeta
    async function deleteItem(itemPath, itemType) {
        const token = localStorage.getItem('access_token');
        const data = {
            target_path: itemPath
        };

        try {
            const response = await fetch('http://127.0.0.1:5000/file/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`  // Incluir el token JWT
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (response.ok) {
                console.log(result.message);
                fetchDirectoryContent(currentPath);  // Recargar el contenido actual del directorio
            } else {
                console.error(result.error);
                alert(result.error || 'Error al eliminar el archivo o carpeta.');
            }
        } catch (error) {
            console.error('Error al eliminar el archivo o carpeta:', error);
        }
    }

    // Función para descargar un archivo
    async function downloadFile(filePath) {
        const token = localStorage.getItem('access_token');

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
            } else {
                const errorData = await response.json();
                alert(errorData.error || 'Error al descargar el archivo.');
            }
        } catch (error) {
            console.error('Error al descargar el archivo:', error);
        }
    }

    // Función para descargar una carpeta como ZIP
    async function downloadFolder(folderPath) {
        const token = localStorage.getItem('access_token');

        try {
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
            } else {
                const errorData = await response.json();
                alert(errorData.error || 'Error al descargar la carpeta.');
            }
        } catch (error) {
            console.error('Error al descargar la carpeta:', error);
        }
    }

    // Funcionalidad del botón de regresar a dashboard
    backButton.addEventListener('click', function () {
        window.location.href = 'dashboard.html'; // Redirigir a la página del dashboard
    });

    // Inicializar mostrando la raíz del directorio
    fetchDirectoryContent('');
});
