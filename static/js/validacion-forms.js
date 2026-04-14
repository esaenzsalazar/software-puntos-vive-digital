/**
 * Inicializador de Validación para Formularios PVD
 * Contrato CD-224-2026 - Alcaldía de Bugalagrande
 * 
 * Este archivo agrega validaciones automáticas a los formularios comunes
 */

document.addEventListener('DOMContentLoaded', function() {
    inicializarValidacionCiudadano();
    inicializarValidacionAtencion();
    inicializarValidacionRecurso();
    inicializarValidacionSala();
});

/**
 * Validación para formulario de Ciudadano
 */
function inicializarValidacionCiudadano() {
    const formCiudadano = document.querySelector('form');
    if (!formCiudadano) return;

    // Validar número de documento
    const numdocInput = document.querySelector('[name="ciu_numdoc"]');
    if (numdocInput) {
        numdocInput.addEventListener('input', function() {
            // Solo permitir números
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarDocumento, 'Número de documento');
            }
        });
        numdocInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarDocumento, 'Número de documento');
            }
        });
    }

    // Validar nombres
    const nombresInput = document.querySelector('[name="ciu_nmbres"]');
    if (nombresInput) {
        nombresInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNombre, 'Nombres');
            }
        });
    }

    // Validar apellidos
    const apellidosInput = document.querySelector('[name="ciu_aplldos"]');
    if (apellidosInput) {
        apellidosInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNombre, 'Apellidos');
            }
        });
    }

    // Validar teléfono
    const tlfnoInput = document.querySelector('[name="ciu_tlfno"]');
    if (tlfnoInput) {
        tlfnoInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarTelefono, 'Teléfono');
            }
        });
        tlfnoInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarTelefono, 'Teléfono');
            }
        });
    }

    // Validar email
    const emailInput = document.querySelector('[name="ciu_email"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarEmail, 'Correo electrónico');
            }
        });
    }
}

/**
 * Validación para formulario de Atención
 */
function inicializarValidacionAtencion() {
    const obsInput = document.querySelector('[name="atn_obs"]');
    if (obsInput) {
        obsInput.addEventListener('blur', function() {
            if (this.value && this.value.length > 0) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarLongitudMaxima.bind(null, 512, 'Observaciones'), 'Observaciones');
            }
        });
    }
}

/**
 * Validación para formulario de Recurso
 */
function inicializarValidacionRecurso() {
    const recCdgoInput = document.querySelector('[name="rec_cdgo"]');
    if (recCdgoInput) {
        recCdgoInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNumerico, 'Código del recurso');
            }
        });
    }
}

/**
 * Validación para formulario de Sala
 */
function inicializarValidacionSala() {
    const salaNombreInput = document.querySelector('[name="sala_nombre"]');
    if (salaNombreInput) {
        salaNombreInput.addEventListener('blur', function() {
            if (this.value) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNombre, 'Nombre de la sala');
            }
        });
    }

    const capacidadInput = document.querySelector('[name="sala_capacidad"]');
    if (capacidadInput) {
        capacidadInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0) {
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNumerico, 'Capacidad');
            }
        });
    }
}
