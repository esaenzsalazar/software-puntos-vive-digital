/**
 * Validación Universal en Tiempo Real — Puntos Vive Digital
 * Se inicializa automáticamente en todas las páginas con formularios.
 */

document.addEventListener('DOMContentLoaded', function() {
    inicializarValidacionUniversal();
    inicializarValidacionCiudadano();
    inicializarValidacionAtencion();
    inicializarValidacionPVD();
    inicializarValidacionSala();
    inicializarValidacionHabilitacion();
});

// ============================================================================
// UTILIDADES COMPARTIDAS
// ============================================================================

function pvdMostrarFeedback(campo, valido, mensaje) {
    pvdLimpiarFeedback(campo);
    campo.classList.remove('pvd-valid', 'pvd-invalid');

    if (valido) {
        campo.classList.add('pvd-valid');
        campo.style.borderColor = '#10b981';
        campo.style.boxShadow = '0 0 0 2px rgba(16,185,129,0.12)';
        const fb = document.createElement('span');
        fb.className = 'pvd-feedback pvd-feedback--ok';
        fb.textContent = '✓';
        fb.style.cssText = 'color:#10b981;font-size:11px;margin-top:2px;display:block;';
        campo.parentElement.appendChild(fb);
    } else if (mensaje) {
        campo.classList.add('pvd-invalid');
        campo.style.borderColor = '#ef4444';
        campo.style.boxShadow = '0 0 0 2px rgba(239,68,68,0.12)';
        const fb = document.createElement('span');
        fb.className = 'pvd-feedback pvd-feedback--error';
        fb.textContent = '⚠ ' + mensaje;
        fb.style.cssText = 'color:#ef4444;font-size:11px;margin-top:2px;display:block;font-weight:500;';
        campo.parentElement.appendChild(fb);
    }
}

function pvdLimpiarFeedback(campo) {
    if (!campo || !campo.parentElement) return;
    campo.parentElement.querySelectorAll('.pvd-feedback').forEach(el => el.remove());
    campo.classList.remove('pvd-valid', 'pvd-invalid');
    campo.style.borderColor = '';
    campo.style.boxShadow = '';
}

function pvdObtenerEtiqueta(campo) {
    if (campo.id) {
        const lbl = document.querySelector(`label[for="${campo.id}"]`);
        if (lbl) return lbl.textContent.replace(/[*]/g, '').trim();
    }
    return (campo.placeholder || campo.name || 'Campo')
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

// ============================================================================
// VALIDACIÓN UNIVERSAL — cubre todos los campos de todos los formularios
// ============================================================================

function inicializarValidacionUniversal() {
    const campos = document.querySelectorAll(
        'input:not([type="hidden"]):not([type="submit"]):not([type="checkbox"]):not([type="radio"]):not([type="button"]),' +
        'textarea, select'
    );

    campos.forEach(function(campo) {
        // Saltar campos ya gestionados por validaciones específicas
        if (campo.dataset.pvdValidado) return;

        const nombre = campo.name || '';
        const tipo   = campo.type  || 'text';

        campo.addEventListener('blur', function() {
            pvdValidarCampoUniversal(this);
        });

        if (campo.tagName === 'SELECT') {
            campo.addEventListener('change', function() {
                pvdValidarCampoUniversal(this);
            });
        }

        // Inputs numéricos: filtrar en tiempo real
        if (tipo === 'number') {
            campo.addEventListener('input', function() {
                pvdValidarCampoUniversal(this);
            });
        }
    });
}

function pvdValidarCampoUniversal(campo) {
    const nombre = campo.name || '';
    const tipo   = campo.type  || 'text';
    const valor  = campo.value;
    const etiqueta = pvdObtenerEtiqueta(campo);

    // Si vacío y no requerido → limpiar
    if (!valor && !campo.required) {
        pvdLimpiarFeedback(campo);
        return;
    }

    // Requerido vacío
    if (campo.required && !valor.trim()) {
        pvdMostrarFeedback(campo, false, `${etiqueta} es requerido`);
        return;
    }

    if (!valor) return;

    let resultado = { valido: true, mensaje: '' };

    // Email
    if (tipo === 'email' || nombre === 'email' || nombre === 'correo') {
        resultado = ValidacionPVD.validarEmail(valor, etiqueta);
    }
    // Teléfono
    else if (nombre === 'telefono' || nombre.includes('phone')) {
        resultado = ValidacionPVD.validarTelefono(valor, etiqueta);
    }
    // Documento
    else if (nombre === 'numero_documento') {
        resultado = ValidacionPVD.validarDocumento(valor, etiqueta);
    }
    // Nombres y apellidos
    else if (['primer_nombre','segundo_nombre','primer_apellido','segundo_apellido','solicitante'].includes(nombre)) {
        if (valor.length < 2) {
            resultado = { valido: false, mensaje: `${etiqueta} debe tener al menos 2 caracteres` };
        }
    }
    // Números enteros positivos
    else if (['capacidad','capacidad_requerida','estrato'].includes(nombre)) {
        const n = parseInt(valor);
        if (isNaN(n) || n < 1) resultado = { valido: false, mensaje: `${etiqueta} debe ser un número mayor a 0` };
    }
    // Calificación 1-5
    else if (nombre === 'calificacion') {
        const n = parseInt(valor);
        if (isNaN(n) || n < 1 || n > 5) resultado = { valido: false, mensaje: 'La calificación debe estar entre 1 y 5' };
    }
    // Textarea: solo límite máximo
    else if (campo.tagName === 'TEXTAREA') {
        const max = parseInt(campo.maxlength || 1000);
        if (valor.length > max) resultado = { valido: false, mensaje: `Máximo ${max} caracteres` };
    }

    pvdMostrarFeedback(campo, resultado.valido, resultado.mensaje);
}

// ============================================================================
// CIUDADANO
// ============================================================================

function inicializarValidacionCiudadano() {
    const numdoc = document.querySelector('[name="numero_documento"]');
    if (numdoc) {
        numdoc.dataset.pvdValidado = '1';
        numdoc.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarDocumento(this.value)));
            else
                pvdLimpiarFeedback(this);
        });
        numdoc.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarDocumento(this.value)));
        });
    }

    const primerNombreCiu = document.querySelector('[name="primer_nombre"]');
    if (primerNombreCiu) {
        primerNombreCiu.dataset.pvdValidado = '1';
        primerNombreCiu.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarNombre(this.value, 'Primer nombre')));
            else if (this.required !== false)
                pvdMostrarFeedback(this, false, 'El primer nombre es requerido');
        });
        primerNombreCiu.addEventListener('input', function() {
            if (this.classList.contains('pvd-invalid'))
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarNombre(this.value, 'Primer nombre')));
        });
    }

    const primerApellidoCiu = document.querySelector('[name="primer_apellido"]');
    if (primerApellidoCiu) {
        primerApellidoCiu.dataset.pvdValidado = '1';
        primerApellidoCiu.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarNombre(this.value, 'Primer apellido')));
            else if (this.required !== false)
                pvdMostrarFeedback(this, false, 'El primer apellido es requerido');
        });
    }

    const tlfno = document.querySelector('[name="telefono"]');
    if (tlfno) {
        tlfno.dataset.pvdValidado = '1';
        tlfno.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').substring(0, 10);
            if (this.value.length > 0)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarTelefono(this.value)));
            else
                pvdLimpiarFeedback(this);
        });
        tlfno.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarTelefono(this.value)));
        });
    }

    const emailCiu = document.querySelector('[name="correo"]');
    if (emailCiu) {
        emailCiu.dataset.pvdValidado = '1';
        emailCiu.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarEmail(this.value)));
            else
                pvdLimpiarFeedback(this);
        });
        emailCiu.addEventListener('input', function() {
            if (this.classList.contains('pvd-invalid'))
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarEmail(this.value)));
        });
    }
}

// ============================================================================
// ATENCIÓN
// ============================================================================

function inicializarValidacionAtencion() {
    const horaIni = document.querySelector('[name="hora_inicio"]');
    const horaFin = document.querySelector('[name="hora_fin"]');

    function validarHoras() {
        if (!horaIni || !horaFin || !horaIni.value || !horaFin.value) return;
        if (horaFin.value <= horaIni.value) {
            pvdMostrarFeedback(horaFin, false, 'La hora de fin debe ser posterior a la hora de inicio');
        } else {
            pvdMostrarFeedback(horaFin, true, '');
        }
    }

    if (horaIni) {
        horaIni.dataset.pvdValidado = '1';
        horaIni.addEventListener('change', validarHoras);
    }
    if (horaFin) {
        horaFin.dataset.pvdValidado = '1';
        horaFin.addEventListener('change', validarHoras);
    }

    const obsInput = document.querySelector('[name="observaciones"]');
    if (obsInput) {
        obsInput.dataset.pvdValidado = '1';
        obsInput.addEventListener('blur', function() {
            const max = 512;
            if (this.value.length > max)
                pvdMostrarFeedback(this, false, `Máximo ${max} caracteres (tienes ${this.value.length})`);
            else if (this.value)
                pvdMostrarFeedback(this, true, '');
            else
                pvdLimpiarFeedback(this);
        });
        obsInput.addEventListener('input', function() {
            const max = 512;
            const restante = max - this.value.length;
            if (this.classList.contains('pvd-invalid') && this.value.length <= max)
                pvdMostrarFeedback(this, true, '');
        });
    }
}

// ============================================================================
// PVD (PUNTO VIVE DIGITAL)
// ============================================================================

function inicializarValidacionPVD() {
    const esPvdForm = document.getElementById('id_direccion') &&
                      document.querySelector('[name="descripcion"]') &&
                      !document.querySelector('[name="numero_documento"]');
    if (!esPvdForm) return;

    const nombrePvd = document.querySelector('[name="nombre"]');
    if (nombrePvd) {
        nombrePvd.dataset.pvdValidado = '1';
        nombrePvd.addEventListener('blur', function() {
            if (this.value.trim().length < 3)
                pvdMostrarFeedback(this, false, 'El nombre debe tener al menos 3 caracteres');
            else
                pvdMostrarFeedback(this, true, '');
        });
    }

    const pvdTlfno = document.querySelector('[name="telefono"]');
    if (pvdTlfno) {
        pvdTlfno.dataset.pvdValidado = '1';
        pvdTlfno.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').substring(0, 10);
        });
        pvdTlfno.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarTelefono(this.value)));
        });
    }

    const pvdCorreo = document.querySelector('[name="correo"]');
    if (pvdCorreo) {
        pvdCorreo.dataset.pvdValidado = '1';
        pvdCorreo.addEventListener('blur', function() {
            if (this.value)
                pvdMostrarFeedback(this, ...desempaquetar(ValidacionPVD.validarEmail(this.value)));
            else
                pvdLimpiarFeedback(this);
        });
    }
}

// ============================================================================
// SALA
// ============================================================================

function inicializarValidacionSala() {
    const esSalaForm = document.querySelector('[name="punto_vive_digital"]') &&
                       document.querySelector('[name="capacidad"]') &&
                       !document.querySelector('[name="tipo_uso"]');
    if (!esSalaForm) return;

    const nombreSala = document.querySelector('[name="nombre"]');
    if (nombreSala) {
        nombreSala.dataset.pvdValidado = '1';
        nombreSala.addEventListener('blur', function() {
            if (this.value.trim().length < 2)
                pvdMostrarFeedback(this, false, 'El nombre de la sala debe tener al menos 2 caracteres');
            else
                pvdMostrarFeedback(this, true, '');
        });
    }

    const capacidad = document.querySelector('[name="capacidad"]');
    if (capacidad) {
        capacidad.dataset.pvdValidado = '1';
        capacidad.addEventListener('blur', function() {
            const n = parseInt(this.value);
            if (isNaN(n) || n < 1)
                pvdMostrarFeedback(this, false, 'La capacidad debe ser al menos 1 persona');
            else if (n > 500)
                pvdMostrarFeedback(this, false, 'La capacidad máxima razonable es 500 personas');
            else
                pvdMostrarFeedback(this, true, '');
        });
    }
}

// ============================================================================
// HABILITACIÓN DE SALA
// ============================================================================

function inicializarValidacionHabilitacion() {
    const esHabForm = document.querySelector('[name="tipo_uso"]') &&
                      document.querySelector('[name="solicitante"]');
    if (!esHabForm) return;

    const horaIni = document.querySelector('[name="hora_inicio"]');
    const horaFin = document.querySelector('[name="hora_fin"]');
    const fecha   = document.querySelector('[name="fecha"]');

    function validarRangoHoras() {
        if (!horaIni || !horaFin || !horaIni.value || !horaFin.value) return;
        if (horaFin.value <= horaIni.value) {
            pvdMostrarFeedback(horaFin, false, 'La hora de fin debe ser posterior a la de inicio');
        } else {
            pvdMostrarFeedback(horaFin, true, '');
        }
    }

    if (horaIni) {
        horaIni.dataset.pvdValidado = '1';
        horaIni.addEventListener('change', validarRangoHoras);
    }
    if (horaFin) {
        horaFin.dataset.pvdValidado = '1';
        horaFin.addEventListener('change', validarRangoHoras);
    }

    if (fecha) {
        fecha.dataset.pvdValidado = '1';
        fecha.addEventListener('change', function() {
            const hoy = new Date().toISOString().split('T')[0];
            if (this.value < hoy)
                pvdMostrarFeedback(this, false, 'La fecha no puede ser anterior a hoy');
            else
                pvdMostrarFeedback(this, true, '');
        });
    }

    const solicitante = document.querySelector('[name="solicitante"]');
    if (solicitante) {
        solicitante.dataset.pvdValidado = '1';
        solicitante.addEventListener('blur', function() {
            if (this.value.trim().length < 2)
                pvdMostrarFeedback(this, false, 'Indica el nombre del solicitante (mínimo 2 caracteres)');
            else
                pvdMostrarFeedback(this, true, '');
        });
    }

    const capReq = document.querySelector('[name="capacidad_requerida"]');
    if (capReq) {
        capReq.dataset.pvdValidado = '1';
        capReq.addEventListener('blur', function() {
            if (this.value) {
                const n = parseInt(this.value);
                if (isNaN(n) || n < 1)
                    pvdMostrarFeedback(this, false, 'Debe ser al menos 1 persona');
                else
                    pvdMostrarFeedback(this, true, '');
            } else {
                pvdLimpiarFeedback(this);
            }
        });
    }
}

// ============================================================================
// HELPER: desempaquetar resultado { valido, mensaje } → [valido, mensaje]
// ============================================================================
function desempaquetar(resultado) {
    return [resultado.valido, resultado.mensaje];
}
