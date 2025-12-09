// login.js - Manejo del formulario de inicio de sesión
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        container.style.transition = 'all 0.5s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    }, 100);

    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');
    const forgotPasswordLink = document.getElementById('forgotPassword');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value
        };
        
        // Validaciones básicas
        if (!formData.username || !formData.password) {
            showMessage('Por favor, completa todos los campos', 'error');
            return;
        }
        
        // Mostrar estado de carga
        const submitButton = loginForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando sesión...';
        submitButton.disabled = true;
        
        try {
            const response = await fetch('http://localhost:8000/auth/login/json', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                credentials: 'include', // Para manejar cookies si es necesario
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                // Intentar parsear el error
                let errorMessage = 'Error en el inicio de sesión';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    errorMessage = `Error ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            showMessage('¡Inicio de sesión exitoso!', 'success');
            
            // Guardar token si está presente en la respuesta
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify({
                    username: formData.username,
                    // Guardar otros datos del usuario si vienen en la respuesta
                    ...data
                }));
            }
            
            // Redirigir al dashboard o página principal después de 1 segundo
            setTimeout(() => {
                redirectToDashboard();
            }, 1000);
            
        } catch (error) {
            console.error('Error completo:', error);
            showMessage('Error: ' + error.message, 'error');
        } finally {
            // Restaurar botón
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    });
    
    // Manejar "Olvidé mi contraseña"
    forgotPasswordLink.addEventListener('click', function(e) {
        e.preventDefault();
        showMessage('Función de recuperación de contraseña no implementada aún.', 'error');
    });
});

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 3000);
    } else {
        // Para errores, ocultar después de 5 segundos
        setTimeout(() => {
            messageDiv.classList.add('hidden');
        }, 5000);
    }
}

function redirectToRegister() {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        window.location.href = 'register.html';
    }, 300);
}

function redirectToDashboard() {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        // Cambia 'dashboard.html' por la página a la que quieres redirigir después del login
        window.location.href = 'dashboard.html';
    }, 300);
}

// Validación en tiempo real
document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    function validateForm() {
        if (usernameInput.value.trim() && passwordInput.value) {
            // Aquí podrías agregar validaciones adicionales si es necesario
        }
    }
    
    usernameInput.addEventListener('input', validateForm);
    passwordInput.addEventListener('input', validateForm);
});

// Verificar si ya hay una sesión activa al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Si hay token, podrías redirigir directamente al dashboard
        // o mostrar un mensaje de que ya hay sesión activa
        // Descomenta la siguiente línea si quieres redirigir automáticamente:
        // redirectToDashboard();
    }
});