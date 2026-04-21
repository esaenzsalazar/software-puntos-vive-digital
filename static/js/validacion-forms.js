/**
 * Inicializador de Validación para Formularios PVD
 * Contrato CD-224-2026 - Alcaldía de Bugalagrande
 */

document.addEventListener('DOMContentLoaded', function() {
    inicializarValidacionCiudadano();
    inicializarValidacionAtencion();
    inicializarValidacionPVD();
});

function inicializarValidacionCiudadano() {
    const numdocInput = document.querySelector('[name="numero_documento"]');
    if (numdocInput) {
        numdocInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 0)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarDocumento, 'Número de documento');
        });
        numdocInput.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarDocumento, 'Número de documento');
        });
    }

    const primerNombreInput = document.querySelector('[name="primer_nombre"]');
    if (primerNombreInput) {
        primerNombreInput.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNombre, 'Primer nombre');
        });
    }

    const primerApellidoInput = document.querySelector('[name="primer_apellido"]');
    if (primerApellidoInput) {
        primerApellidoInput.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarNombre, 'Primer apellido');
        });
    }

    const tlfnoInput = document.querySelector('[name="telefono"]');
    if (tlfnoInput) {
        tlfnoInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').substring(0, 10);
            if (this.value.length > 0)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarTelefono, 'Teléfono');
        });
        tlfnoInput.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarTelefono, 'Teléfono');
        });
    }

    const emailInput = document.querySelector('[name="correo"]');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarEmail, 'Correo electrónico');
        });
        emailInput.addEventListener('input', function() {
            if (this.classList.contains('input-error'))
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarEmail, 'Correo electrónico');
        });
    }
}

function inicializarValidacionAtencion() {
    const obsInput = document.querySelector('[name="observaciones"]');
    if (obsInput) {
        obsInput.addEventListener('blur', function() {
            if (this.value && this.value.length > 512) {
                ValidacionPVD.mostrarError(this, 'Las observaciones no pueden superar los 512 caracteres');
            } else {
                ValidacionPVD.ocultarError(this);
            }
        });
    }
}

function inicializarValidacionPVD() {
    // Solo activo si estamos en el form de PVD (tiene id_nombre y no es el form de ciudadano)
    const nombreInput = document.querySelector('[name="nombre"]');
    const pvdTlfno = document.querySelector('[name="telefono"]');
    const pvdCorreo = document.querySelector('[name="correo"]');

    // Identificar si es el form de PVD por presencia del hidden #id_direccion sin barrio select
    const esPvdForm = document.getElementById('id_direccion') &&
                      document.querySelector('[name="descripcion"]') &&
                      !document.querySelector('[name="numero_documento"]');

    if (!esPvdForm) return;

    if (nombreInput) {
        nombreInput.addEventListener('blur', function() {
            ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarRequerido, 'Nombre del PVD');
        });
    }

    if (pvdTlfno) {
        pvdTlfno.addEventListener('blur', function() {
            ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarTelefono, 'Teléfono');
        });
    }

    if (pvdCorreo) {
        pvdCorreo.addEventListener('blur', function() {
            if (this.value)
                ValidacionPVD.validarYMostrar(this, ValidacionPVD.validarEmail, 'Correo electrónico');
        });
    }
}
