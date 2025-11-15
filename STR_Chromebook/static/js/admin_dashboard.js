/* =================================================================
   SCRIPT PARA EL DASHBOARD DEL ADMINISTRADOR
   (templates/administrador/dashboard.html)
   
   Maneja:
   - Pestañas (Tabs) de reservas
   - Lógica de Aprobar/Rechazar/Ver Detalle
   - Funciones de modales
   - Obtención de Cookie CSRF
================================================================= */

// --- VARIABLES GLOBALES ---
let reservaIdParaRechazar = null;

// --- FUNCIONES GLOBALES (para onclick) ---
// Se asignan a 'window' para ser accesibles
// desde el HTML después de que el DOM cargue.

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.aprobarReserva = function(reservaId) {
    if (!confirm('¿Está seguro de aprobar esta reserva?')) {
        return;
    }

    // ¡URL CORREGIDA! (Sin /gestion/)
    fetch(`/reserva/${reservaId}/aprobar/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al aprobar la reserva');
    });
}

window.mostrarModalRechazo = function(reservaId) {
    reservaIdParaRechazar = reservaId;
    document.getElementById('motivo-rechazo').value = '';
    document.getElementById('error-rechazo').style.display = 'none';
    document.getElementById('modal-rechazo').classList.add('is-active');
}

window.cerrarModalRechazo = function() {
    document.getElementById('modal-rechazo').classList.remove('is-active');
    reservaIdParaRechazar = null;
}

window.confirmarRechazo = function() {
    const motivo = document.getElementById('motivo-rechazo').value.trim();
    const errorDiv = document.getElementById('error-rechazo');

    if (!motivo) {
        errorDiv.textContent = 'Debe proporcionar un motivo para el rechazo';
        errorDiv.style.display = 'block';
        return;
    }

    // ¡URL CORREGIDA! (Sin /gestion/)
    fetch(`/reserva/${reservaIdParaRechazar}/rechazar/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ motivo: motivo })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            cerrarModalRechazo();
            location.reload();
        } else {
            errorDiv.textContent = 'Error: ' + data.error;
            errorDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        errorDiv.textContent = 'Error al rechazar la reserva';
        errorDiv.style.display = 'block';
    });
}

window.verDetalle = function(reservaId) {
    // Mostrar modal
    document.getElementById('modal-detalle').classList.add('is-active');
    document.getElementById('detalle-id').textContent = `#${reservaId}`;
    document.getElementById('detalle-loading').style.display = 'block';
    document.getElementById('detalle-contenido').style.display = 'none';
    document.getElementById('detalle-error').style.display = 'none';

    // ¡URL CORREGIDA! (Sin /gestion/)
    fetch(`/reserva/${reservaId}/detalle/`)
        .then(response => {
            if (!response.ok) {
                // Esta vez, el error 404 es real
                throw new Error(`Error HTTP ${response.status}: No se encontró la URL. Revisa que 'Gestion_Equipos.urls' esté en 'path('', ...)'`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const r = data.reserva;

                // Estado con icono y color
                let estadoHTML = '';
                let iconoHTML = '';
                
                if (r.estado === 'Pendiente') {
                    estadoHTML = '<span class="tag is-warning is-large">⏳ Pendiente</span>';
                    iconoHTML = '<i class="fas fa-clock fa-3x has-text-warning"></i>';
                } else if (r.estado === 'Aprobada') {
                    estadoHTML = '<span class="tag is-success is-large">✅ Aprobada</span>';
                    iconoHTML = '<i class="fas fa-check-circle fa-3x has-text-success"></i>';
                } else if (r.estado === 'Rechazada') {
                    estadoHTML = '<span class="tag is-danger is-large">❌ Rechazada</span>';
                    iconoHTML = '<i class="fas fa-times-circle fa-3x has-text-danger"></i>';
                } else if (r.estado === 'Finalizada') { // Estado añadido
                    estadoHTML = '<span class="tag is-dark is-large">🏁 Finalizada</span>';
                    iconoHTML = '<i class="fas fa-check-double fa-3x has-text-dark"></i>';
                }

                document.getElementById('detalle-estado').innerHTML = estadoHTML;
                document.getElementById('detalle-estado-icon').innerHTML = iconoHTML;

                // Información de la reserva
                document.getElementById('detalle-fecha').textContent = r.fecha_uso;
                document.getElementById('detalle-horario').textContent = `${r.hora_inicio} - ${r.hora_fin}`;
                document.getElementById('detalle-cantidad').innerHTML = `<span class="tag is-info is-medium">${r.cant_solicitada} Chromebooks</span>`;
                document.getElementById('detalle-responsable').textContent = r.responsable_entrega;
                document.getElementById('detalle-telefono-contacto').textContent = r.telefono_contacto;

                // Información académica
                document.getElementById('detalle-docente').textContent = r.docente.nombre;
                document.getElementById('detalle-email').innerHTML = `<a href="mailto:${r.docente.email}">${r.docente.email}</a>`;
                document.getElementById('detalle-telefono').textContent = r.docente.telefono;
                document.getElementById('detalle-facultad').textContent = r.facultad;
                document.getElementById('detalle-carrera').textContent = r.carrera;
                document.getElementById('detalle-asignatura').textContent = r.asignatura;

                // Ubicación
                document.getElementById('detalle-bloque').textContent = r.bloque;
                document.getElementById('detalle-aula').textContent = r.aula;

                // Motivo de rechazo (solo si está rechazada)
                const motivoContainer = document.getElementById('detalle-motivo-rechazo-container');
                if (r.estado === 'Rechazada' && r.motivo_rechazo) {
                    document.getElementById('detalle-motivo-rechazo').textContent = r.motivo_rechazo;
                    motivoContainer.style.display = 'block';
                } else {
                    motivoContainer.style.display = 'none';
                }

                // Mostrar contenido
                document.getElementById('detalle-loading').style.display = 'none';
                document.getElementById('detalle-contenido').style.display = 'block';
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('detalle-loading').style.display = 'none';
            document.getElementById('detalle-error').textContent = 'Error al cargar los detalles: ' + error.message;
            document.getElementById('detalle-error').style.display = 'block';
        });
}

window.cerrarModalDetalle = function() {
    document.getElementById('modal-detalle').classList.remove('is-active');
}

// --- CÓDIGO QUE SE EJECUTA AL CARGAR LA PÁGINA ---
document.addEventListener('DOMContentLoaded', function() {

    // Manejar pestañas
    const tabs = document.querySelectorAll('.tabs li');
    const tabContents = document.querySelectorAll('.tab-content');

    if (tabs.length > 0 && tabContents.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                tabs.forEach(t => t.classList.remove('is-active'));
                tabContents.forEach(c => c.classList.remove('is-active'));
                
                this.classList.add('is-active');
                const tabName = this.getAttribute('data-tab');
                const tabContent = document.getElementById(`tab-${tabName}`);
                if (tabContent) {
                    tabContent.classList.add('is-active');
                }
            });
        });
    }

    // --- MANEJO DE CIERRE DE MODALES ---
    function closeModal($el) {
        if ($el) {
            $el.classList.remove('is-active');
        }
    }

    (document.querySelectorAll('.delete') || []).forEach(($delete) => {
        const $target = $delete.closest('.modal');
        $delete.addEventListener('click', () => {
            closeModal($target);
        });
    });

    (document.querySelectorAll('.modal-background') || []).forEach(($background) => {
        const $target = $background.closest('.modal');
        $background.addEventListener('click', () => {
            closeModal($target);
        });
    });

});