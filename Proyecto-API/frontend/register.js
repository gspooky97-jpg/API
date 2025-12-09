// register.js - Versión corregida
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        container.style.transition = 'all 0.5s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    }, 100);

    const registerForm = document.getElementById('registerForm');
    const messageDiv = document.getElementById('message');
    
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            password: document.getElementById('password').value,
            first_name: document.getElementById('firstName').value.trim(),
            last_name: document.getElementById('lastName').value.trim()
        };
        
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validaciones
        if (formData.password !== confirmPassword) {
            showMessage('Las contraseñas no coinciden', 'error');
            return;
        }
        
        if (formData.password.length < 6) {
            showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
            return;
        }
        
        // Mostrar estado de carga
        const submitButton = registerForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner"></i> Registrando...';
        submitButton.disabled = true;
        
        try {
            const response = await fetch('http://localhost:8000/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                mode: 'cors',
                credentials: 'same-origin', // o 'include' si necesitas cookies
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                // Intentar parsear el error
                let errorMessage = 'Error en el registro';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (parseError) {
                    errorMessage = `Error ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            showMessage('¡Registro exitoso! Redirigiendo al login...', 'success');
            
            // Redirigir después de 2 segundos
            setTimeout(() => {
                redirectToLogin();
            }, 2000);
            
        } catch (error) {
            console.error('Error completo:', error);
            showMessage('Error: ' + error.message, 'error');
        } finally {
            // Restaurar botón
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
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
        }, 5000);
    }
}

function redirectToLogin() {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 300);
}

// Validación en tiempo real para contraseñas
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    function validatePasswords() {
        if (passwordInput.value && confirmPasswordInput.value) {
            if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.style.borderColor = '#dc3545';
            } else {
                confirmPasswordInput.style.borderColor = '#28a745';
            }
        } else {
            confirmPasswordInput.style.borderColor = '#e1e5ee';
        }
    }
    
    passwordInput.addEventListener('input', validatePasswords);
    confirmPasswordInput.addEventListener('input', validatePasswords);
});