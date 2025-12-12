// frontend/dashboard.js

let currentPage = 1;
let totalPages = 1;
const pageSize = 10;

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Mostrar nombre de usuario
    document.getElementById('username').textContent = user.username || 'Usuario';

    // Cargar usuarios y vulnerabilidades
    loadUsers(currentPage);
    loadVulnerabilities();
    
    // Setup forms
    setupCreateUserForm();
    setupCreateVulnForm();
});

// ===== USUARIOS =====

async function loadUsers(page) {
    const token = localStorage.getItem('access_token');
    
    try {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('usersTable').style.display = 'none';
        
        const response = await fetch(`/users?page=${page}&page_size=${pageSize}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            showMessage('Sesión expirada. Por favor, inicia sesión de nuevo.', 'error');
            setTimeout(() => {
                localStorage.clear();
                window.location.href = '/login';
            }, 2000);
            return;
        }

        if (response.status === 403) {
            showMessage('No tienes permisos de administrador.', 'error');
            return;
        }

        if (!response.ok) {
            throw new Error('Error al cargar usuarios');
        }

        const data = await response.json();
        
        currentPage = data.page;
        totalPages = Math.ceil(data.total / data.page_size);
        
        renderUsersTable(data.users);
        updatePagination();
        
        document.getElementById('loading').style.display = 'none';
        document.getElementById('usersTable').style.display = 'table';
        document.getElementById('pagination').style.display = 'flex';

    } catch (error) {
        console.error('Error:', error);
        showMessage('Error al cargar usuarios: ' + error.message, 'error');
        document.getElementById('loading').style.display = 'none';
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('usersBody');
    tbody.innerHTML = '';

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 40px; color: #718096;">No hay usuarios para mostrar</td></tr>';
        return;
    }

    users.forEach(user => {
        const tr = document.createElement('tr');
        
        const rolesBadges = user.roles
            .filter(r => !r.includes('default') && !r.includes('offline') && !r.includes('uma'))
            .map(role => {
                let badgeClass = 'badge-visor';
                if (role === 'Administrador') badgeClass = 'badge-admin';
                if (role === 'Moderador') badgeClass = 'badge-moderator';
                return `<span class="badge ${badgeClass}">${role}</span>`;
            })
            .join(' ');

        const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || '-';
        const statusIcon = user.is_active ? '✅' : '❌';
        const statusText = user.is_active ? 'Activo' : 'Inactivo';
        
        tr.innerHTML = `
            <td><strong>${user.username}</strong></td>
            <td>${user.email}</td>
            <td>${fullName}</td>
            <td>${rolesBadges || '<span class="badge badge-visor">Sin roles</span>'}</td>
            <td>${statusIcon} ${statusText}</td>
            <td>${new Date(user.created_at).toLocaleDateString('es-ES')}</td>
            <td>
                <button class="action-btn btn-edit" onclick="editUser('${user.id}', '${user.username}')">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="action-btn btn-delete" onclick="deleteUser('${user.id}', '${user.username}')">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

function updatePagination() {
    document.getElementById('pageInfo').textContent = `Página ${currentPage} de ${totalPages}`;
    document.getElementById('prevBtn').disabled = currentPage === 1;
    document.getElementById('nextBtn').disabled = currentPage === totalPages;
}

function changePage(delta) {
    const newPage = currentPage + delta;
    if (newPage >= 1 && newPage <= totalPages) {
        loadUsers(newPage);
    }
}

async function editUser(userId, username) {
    const newRole = prompt(
        `Cambiar rol de ${username}:\n\n1. Administrador\n2. Moderador\n3. Visor\n\nIngresa el número:`
    );
    
    const roleMap = {
        '1': 'Administrador',
        '2': 'Moderador',
        '3': 'Visor'
    };

    const role = roleMap[newRole];
    
    if (!role) {
        showMessage('Rol inválido', 'error');
        return;
    }

    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                roles: [role],
                is_active: true
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al actualizar usuario');
        }

        showMessage(`Rol de ${username} actualizado a ${role}`, 'success');
        loadUsers(currentPage);

    } catch (error) {
        console.error('Error:', error);
        showMessage('Error: ' + error.message, 'error');
    }
}

async function deleteUser(userId, username) {
    if (!confirm(`¿Estás seguro de eliminar al usuario "${username}"?\n\nEsta acción no se puede deshacer.`)) {
        return;
    }

    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch(`/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar usuario');
        }

        showMessage(`Usuario ${username} eliminado correctamente`, 'success');
        
        if (currentPage > 1 && document.getElementById('usersBody').children.length === 1) {
            loadUsers(currentPage - 1);
        } else {
            loadUsers(currentPage);
        }

    } catch (error) {
        console.error('Error:', error);
        showMessage('Error: ' + error.message, 'error');
    }
}

function showCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'flex';
}

function closeCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'none';
    document.getElementById('createUserForm').reset();
}

function setupCreateUserForm() {
    const createForm = document.getElementById('createUserForm');
    
    if (createForm) {
        createForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const password = document.getElementById('newPassword').value;
            const passwordConfirm = document.getElementById('newPasswordConfirm').value;
            
            if (password !== passwordConfirm) {
                showMessage('Las contraseñas no coinciden', 'error');
                return;
            }
            
            if (password.length < 12) {
                showMessage('La contraseña debe tener al menos 12 caracteres', 'error');
                return;
            }
            
            const hasUpperCase = /[A-Z]/.test(password);
            const hasLowerCase = /[a-z]/.test(password);
            const hasNumber = /[0-9]/.test(password);
            const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password);
            
            if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecial) {
                showMessage('La contraseña debe contener: mayúsculas, minúsculas, números y caracteres especiales', 'error');
                return;
            }
            
            const userData = {
                username: document.getElementById('newUsername').value.trim(),
                email: document.getElementById('newEmail').value.trim(),
                first_name: document.getElementById('newFirstName').value.trim(),
                last_name: document.getElementById('newLastName').value.trim(),
                password: password
            };
            
            const token = localStorage.getItem('access_token');
            
            try {
                const response = await fetch('/auth/register', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Error al crear usuario');
                }
                
                const data = await response.json();
                
                showMessage(`Usuario ${data.username} creado correctamente`, 'success');
                closeCreateUserModal();
                loadUsers(currentPage);
                
            } catch (error) {
                console.error('Error:', error);
                showMessage('Error: ' + error.message, 'error');
            }
        });
    }
}

// ===== VULNERABILIDADES =====

async function loadVulnerabilities() {
    const token = localStorage.getItem('access_token');

    try {
        const res = await fetch('/stats', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 401) {
            showMessage('Sesión expirada. Vuelve a iniciar sesión.', 'error');
            return;
        }

        if (!res.ok) {
            throw new Error('Error al cargar vulnerabilidades');
        }

        const data = await res.json();
        renderVulnTable(data.vulnerabilities);

        document.getElementById('vulnLoading').style.display = 'none';
        document.getElementById('vulnTable').style.display = 'table';

    } catch (e) {
        console.error(e);
        showMessage('Error al cargar vulnerabilidades: ' + e.message, 'error');
        document.getElementById('vulnLoading').style.display = 'none';
    }
}

function renderVulnTable(vulns) {
    const tbody = document.getElementById('vulnBody');
    tbody.innerHTML = '';

    if (!vulns.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:20px; color:#718096;">No hay vulnerabilidades registradas</td></tr>';
        return;
    }

    vulns.forEach(v => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${v.vuln_id}</td>
            <td>${v.title}</td>
            <td>${v.device_ip}<br><small>${v.device_subnet}</small></td>
            <td>${v.device_mac}</td>
            <td>${v.cvss_score.toFixed(1)}</td>
            <td>${v.severity}</td>
            <td>${v.vuln_type}</td>
            <td>${new Date(v.detected_at).toLocaleString('es-ES')}</td>
        `;
        tbody.appendChild(tr);
    });
}

function showCreateVulnModal() {
    document.getElementById('createVulnModal').style.display = 'flex';
}

function closeCreateVulnModal() {
    document.getElementById('createVulnModal').style.display = 'none';
    document.getElementById('createVulnForm').reset();
}

function setupCreateVulnForm() {
    const form = document.getElementById('createVulnForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const token = localStorage.getItem('access_token');

        const detectedAtValue = document.getElementById('vulnDetectedAt').value;
        const detectedAt = new Date(detectedAtValue);

        const payload = {
            vuln_id: document.getElementById('vulnId').value.trim(),
            title: document.getElementById('vulnTitle').value.trim(),
            device_ip: document.getElementById('vulnIp').value.trim(),
            device_subnet: document.getElementById('vulnSubnet').value.trim(),
            device_mac: document.getElementById('vulnMac').value.trim(),
            cvss_score: parseFloat(document.getElementById('vulnCvss').value),
            severity: document.getElementById('vulnSeverity').value,
            cve_id: document.getElementById('vulnCve').value.trim() || null,
            vuln_type: document.getElementById('vulnType').value.trim(),
            detected_at: detectedAt.toISOString()
        };

        // Validaciones básicas
        if (!payload.vuln_id || !payload.title) {
            showVulnModalMessage('ID y título son obligatorios', 'error');
            return;
        }

        if (isNaN(payload.cvss_score) || payload.cvss_score < 0 || payload.cvss_score > 10) {
            showVulnModalMessage('CVSS debe estar entre 0 y 10', 'error');
            return;
        }

        if (!payload.severity) {
            showVulnModalMessage('Debes seleccionar una severidad', 'error');
            return;
        }

        try {
            const res = await fetch('/stats/vulnerabilidades', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            // Manejar diferentes códigos de error
            if (res.status === 401) {
                showVulnModalMessage('Sesión expirada. Redirigiendo al login...', 'error');
                setTimeout(() => {
                    localStorage.clear();
                    window.location.href = '/login';
                }, 2000);
                return;
            }

            if (res.status === 403) {
                showVulnModalMessage('No tienes permisos para crear vulnerabilidades.', 'error');
                return;
            }

            if (res.status === 409) {
                const err = await res.json();
                showVulnModalMessage(err.detail || 'El ID de vulnerabilidad ya existe', 'error');
                return;
            }

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                showVulnModalMessage(err.detail || 'No se pudo crear la vulnerabilidad', 'error');
                return;
            }

            // Éxito
            const data = await res.json();
            showMessage(`Vulnerabilidad ${data.vuln_id} creada correctamente`, 'success');
            closeCreateVulnModal();
            loadVulnerabilities();

        } catch (e) {
            console.error('Error creando vulnerabilidad:', e);
            showVulnModalMessage('Error de conexión: ' + e.message, 'error');
        }
    });
}


// ===== UTILIDADES =====

function logout() {
    if (confirm('¿Seguro que deseas cerrar sesión?')) {
        localStorage.clear();
        window.location.href = '/login';
    }
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove('hidden');
    
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 5000);
}

// Función para mostrar mensajes dentro del modal de vulnerabilidades
function showVulnModalMessage(text, type) {
    const messageDiv = document.getElementById('vulnModalMessage');
    messageDiv.textContent = text;
    messageDiv.className = `modal-message ${type}`;
    messageDiv.classList.remove('hidden');
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 5000);
}

// Actualizar closeCreateVulnModal para limpiar mensajes
function closeCreateVulnModal() {
    document.getElementById('createVulnModal').style.display = 'none';
    document.getElementById('createVulnForm').reset();
    // Limpiar mensaje del modal
    const messageDiv = document.getElementById('vulnModalMessage');
    if (messageDiv) {
        messageDiv.classList.add('hidden');
    }
}
