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
            // CAMBIADO: /auth/login en lugar de /auth/login/json
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
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

            // CAMBIADO: Guardar 'token' en lugar de 'access_token'
            if (data.token) {
                localStorage.setItem('access_token', data.token);
                localStorage.setItem('user', JSON.stringify({
                    id: data.id,
                    username: data.username,
                    email: data.email
                }));
            }

            // Redirigir al dashboard
            setTimeout(() => {
                redirectToDashboard();
            }, 1000);

        } catch (error) {
            console.error('Error completo:', error);
            showMessage('Error: ' + error.message, 'error');
        } finally {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    });

    // Manejar "Olvidé mi contraseña"
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            showMessage('Función de recuperación de contraseña no implementada aún.', 'error');
        });
    }
});

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove('hidden');
    
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, type === 'success' ? 3000 : 5000);
}

function redirectToRegister() {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    setTimeout(() => {
        window.location.href = '/register';
    }, 300);
}

function redirectToDashboard() {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    setTimeout(() => {
        window.location.href = '/dashboard';  // ← Cambiar aquí
    }, 300);
}


// Verificar si ya hay sesión activa
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Opcional: redirigir automáticamente si ya hay sesión
        // redirectToDashboard();
    }
});
