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

        if (formData.password.length < 12) {
            showMessage('La contraseña debe tener al menos 12 caracteres', 'error');
            return;
        }

        // Validación de complejidad de contraseña
        const hasUpperCase = /[A-Z]/.test(formData.password);
        const hasLowerCase = /[a-z]/.test(formData.password);
        const hasNumber = /[0-9]/.test(formData.password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.password);

        if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecial) {
            showMessage('La contraseña debe contener: mayúsculas, minúsculas, números y caracteres especiales', 'error');
            return;
        }

        // Mostrar estado de carga
        const submitButton = registerForm.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Registrando...';
        submitButton.disabled = true;

        try {
            console.log('Enviando datos:', formData);

            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            console.log('Status:', response.status);

            if (!response.ok) {
                let errorMessage = 'Error en el registro';
                
                try {
                    const errorData = await response.json();
                    console.log('Error data:', errorData);
                    
                    // Manejar diferentes formatos de error
                    if (errorData.detail) {
                        // Si detail es un array (validación de Pydantic)
                        if (Array.isArray(errorData.detail)) {
                            errorMessage = errorData.detail.map(err => {
                                const field = err.loc ? err.loc.join('.') : 'campo';
                                return `${field}: ${err.msg}`;
                            }).join(', ');
                        } 
                        // Si detail es un string
                        else if (typeof errorData.detail === 'string') {
                            errorMessage = errorData.detail;
                        }
                        // Si detail es un objeto
                        else {
                            errorMessage = JSON.stringify(errorData.detail);
                        }
                    }
                } catch (parseError) {
                    console.error('Error parseando JSON:', parseError);
                    errorMessage = `Error ${response.status}: ${response.statusText}`;
                }
                
                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log('Registro exitoso:', data);
            
            showMessage('¡Registro exitoso! Redirigiendo al login...', 'success');

            setTimeout(() => {
                redirectToLogin();
            }, 2000);

        } catch (error) {
            console.error('Error completo:', error);
            showMessage('Error: ' + error.message, 'error');
        } finally {
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
        window.location.href = '/login';
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

    if (passwordInput && confirmPasswordInput) {
        passwordInput.addEventListener('input', validatePasswords);
        confirmPasswordInput.addEventListener('input', validatePasswords);
    }
});
