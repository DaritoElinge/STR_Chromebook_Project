// =================================================================
// JAVASCRIPT PARA LA PÁGINA DE CREAR RESERVA (docente/crear_reserva.html)
// =================================================================

// Envolvemos todo en DOMContentLoaded para asegurar que el HTML esté cargado
// antes de buscar los elementos (IDs).
document.addEventListener('DOMContentLoaded', function() {

    // ===================================================
    // AUTOCOMPLETAR RESPONSABLE
    // ===================================================
    const responsableInput = document.getElementById('id_responsable_entrega');
    const autocompleteList = document.getElementById('autocomplete-list');
    
    // "Guardia" - Solo ejecutar si los elementos existen en la página
    if (responsableInput && autocompleteList) { 
        let currentFocus = -1;

        responsableInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length < 2) {
                autocompleteList.style.display = 'none';
                return;
            }

            // Llamar a la API de autocompletado
            fetch(`/api/autocompletar-responsable/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    autocompleteList.innerHTML = '';
                    
                    if (data.results.length === 0) {
                        autocompleteList.style.display = 'none';
                        return;
                    }

                    data.results.forEach((nombre, index) => {
                        const div = document.createElement('div');
                        div.className = 'autocomplete-suggestion';
                        div.textContent = nombre;
                        div.addEventListener('click', function() {
                            responsableInput.value = nombre;
                            autocompleteList.style.display = 'none';
                        });
                        autocompleteList.appendChild(div);
                    });

                    autocompleteList.style.display = 'block';
                    currentFocus = -1;
                })
                .catch(error => console.error('Error:', error));
        });

        // Navegar con teclado
        responsableInput.addEventListener('keydown', function(e) {
            const items = autocompleteList.getElementsByClassName('autocomplete-suggestion');
            
            if (e.keyCode === 40) { // Flecha abajo
                currentFocus++;
                addActive(items);
                e.preventDefault();
            } else if (e.keyCode === 38) { // Flecha arriba
                currentFocus--;
                addActive(items);
                e.preventDefault();
            } else if (e.keyCode === 13) { // Enter
                e.preventDefault();
                if (currentFocus > -1 && items[currentFocus]) {
                    items[currentFocus].click();
                }
            } else if (e.keyCode === 27) { // Escape
                autocompleteList.style.display = 'none';
            }
        });

        function addActive(items) {
            if (!items || items.length === 0) return;
            removeActive(items);
            if (currentFocus >= items.length) currentFocus = 0;
            if (currentFocus < 0) currentFocus = items.length - 1;
            items[currentFocus].classList.add('active');
        }

        function removeActive(items) {
            for (let i = 0; i < items.length; i++) {
                items[i].classList.remove('active');
            }
        }

        // Cerrar autocompletado al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (e.target !== responsableInput) {
                autocompleteList.style.display = 'none';
            }
        });
    } // Fin de la guardia de Autocompletar

    // ===================================================
    // FILTRAR AULAS POR BLOQUE
    // ===================================================
    const bloqueSelect = document.getElementById('id_bloque');
    const aulaSelect = document.getElementById('id_id_aula');

    // "Guardia" - Solo ejecutar si los elementos existen
    if (bloqueSelect && aulaSelect) { 
        bloqueSelect.addEventListener('change', function() {
            const bloqueId = this.value;
            
            if (!bloqueId) {
                aulaSelect.innerHTML = '<option value="">Seleccione un aula</option>';
                return;
            }

            // Llamar a la API para filtrar aulas
            fetch(`/api/filtrar-aulas/?bloque_id=${bloqueId}`)
                .then(response => response.json())
                .then(data => {
                    aulaSelect.innerHTML = '<option value="">Seleccione un aula</option>';
                    
                    data.aulas.forEach(aula => {
                        const option = document.createElement('option');
                        option.value = aula.id_aula;
                        option.textContent = aula.nom_aula;
                        aulaSelect.appendChild(option);
                    });
                })
                .catch(error => console.error('Error:', error));
        });
    } // Fin de la guardia de Aulas

    // ===================================================
    // CONVERTIR RESPONSABLE A MAYÚSCULAS AL ENVIAR
    // ===================================================
    const reservaForm = document.getElementById('reserva-form');
    
    // "Guardia" - Solo ejecutar si los elementos existen
    if (reservaForm && responsableInput) { 
        reservaForm.addEventListener('submit', function(e) {
            responsableInput.value = responsableInput.value.toUpperCase();
        });
    } // Fin de la guardia de Submit

    // ===================================================
    // 🆕 FILTRAR ASIGNATURAS POR CARRERA
    
    // ===================================================
    const carreraSelect = document.getElementById('id_carrera');
    const asignaturaSelect = document.getElementById('id_asignatura');

    // "Guardia" - Solo ejecutar si los elementos existen
    if (carreraSelect && asignaturaSelect) { 
        carreraSelect.addEventListener('change', function() {
            const carreraId = this.value;
                    
            console.log('Carrera seleccionada:', carreraId); // Debug
                    
            // Limpiar select de asignaturas
            asignaturaSelect.innerHTML = '<option value="">Seleccione una asignatura</option>';
                    
            if (!carreraId) {
                return;
            }

            // Llamar a la API para filtrar asignaturas
            fetch(`/api/filtrar-asignaturas/?carrera_id=${carreraId}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Asignaturas recibidas:', data); // Debug
                    
                    if (data.asignaturas && data.asignaturas.length > 0) {
                        data.asignaturas.forEach(asignatura => {
                            const option = document.createElement('option');
                            option.value = asignatura.id_asignatura;
                            option.textContent = asignatura.nom_asignatura;
                            asignaturaSelect.appendChild(option);
                        });
                    } else {
                        const option = document.createElement('option');
                        option.value = '';
                        option.textContent = 'No hay asignaturas disponibles';
                        asignaturaSelect.appendChild(option);
                    }
                })
                .catch(error => {
                    console.error('Error al cargar asignaturas:', error);
                    alert('Error al cargar las asignaturas. Por favor, intente nuevamente.');
                });
        });
    } // Fin de la guardia de Asignaturas

}); // Fin de DOMContentLoaded