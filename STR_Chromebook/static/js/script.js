/**
 * Cuando el usuario selecciona un perfil:
 * - cerramos la modal
 * - mostramos el formulario de login que estaba oculto
 * - colocamos el perfil seleccionado en un hidden input y en el badge
 * - cambiamos color del botón principal según el rol
 * - ponemos el foco en el campo usuario
 */
function selectProfile(profile) {
    const modal = document.getElementById('profile-modal');
    const loginBox = document.getElementById('login-box');
    const perfilInput = document.getElementById('perfil-input');
    const badge = document.getElementById('selected-profile');
    const loginButton = document.querySelector('#login-form button[type="submit"]');
    
    // Cerrar modal
    modal.classList.remove('is-active');
    
    // Mostrar login (quitar is-hidden)
    loginBox.classList.remove('is-hidden');
    
    // Guardar perfil en el campo oculto
    perfilInput.value = profile;
    
    // Actualizar badge visible con icon y texto
    let html = '';
    if (profile === 'docente') {
        html = `
            <span class="icon has-text-link"><i class="fas fa-chalkboard-teacher"></i></span>
            <span><strong class="has-text-dark">Docente</strong></span>
        `;
        // Cambiar color del botón principal a azul (docente)
        loginButton.classList.remove('is-warning');
        loginButton.classList.add('is-link');
    } else {
        html = `
            <span class="icon has-text-warning"><i class="fas fa-user-shield"></i></span>
            <span><strong class="has-text-dark">Administrativo</strong></span>
        `;
        // Cambiar color del botón principal a amarillo (administrativo)
        loginButton.classList.remove('is-link');
        loginButton.classList.add('is-warning');
    }
    
    badge.innerHTML = html;
    
    // Foco en usuario (con pequeño delay para asegurar que el elemento es visible)
    setTimeout(() => {
        const u = document.getElementById('username');
        if (u) u.focus();
    }, 120);
}

/**
 * Permite volver al modal de selección de perfil
 * - oculta el formulario de login
 * - muestra nuevamente la modal
 */
function mostrarModalPerfiles() {
    const modal = document.getElementById('profile-modal');
    const loginBox = document.getElementById('login-box');
    
    modal.classList.add('is-active');
    loginBox.classList.add('is-hidden');
}

/**
 * Al cargar la página:
 * - activamos la modal por defecto
 * - nos aseguramos de que el login esté oculto
 */
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('profile-modal');
    const loginBox = document.getElementById('login-box');
    
    if (modal) modal.classList.add('is-active');
    if (loginBox) loginBox.classList.add('is-hidden');
});