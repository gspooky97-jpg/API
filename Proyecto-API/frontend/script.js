function redirectToLogin() {
    // Simulacion de transición suave en redirirección
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 300);
}

function redirectToRegister() {
    // Simulacion de transición suave en redirirección
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        window.location.href = 'register.html';
    }, 300);
}

// Efecto de carga suave
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.container');
    container.style.opacity = '0';
    container.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        container.style.transition = 'all 0.5s ease';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    }, 100);
});