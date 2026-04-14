/**
 * Biblioteca de Validación para Puntos Vive Digital
 * Contrato CD-224-2026 - Alcaldía de Bugalagrande
 * 
 * Funciones de validación reutilizables para formularios
 */

const ValidacionPVD = {
    // ============================================================================
    // VALIDACIONES DE CAMPOS INDIVIDUALES
    // ============================================================================
    
    /**
     * Valida formato de número de documento
     */
    validarDocumento(valor, campoNombre = 'Documento') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: 'El número de documento es requerido' };
        }
        
        valor = valor.trim();
        
        if (!/^\d+$/.test(valor)) {
            return { valido: false, mensaje: 'El documento solo debe contener números' };
        }
        
        if (valor.length < 6) {
            return { valido: false, mensaje: 'El documento debe tener al menos 6 dígitos' };
        }
        
        if (valor.length > 20) {
            return { valido: false, mensaje: 'El documento no puede tener más de 20 dígitos' };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida formato de dirección
     */
    validarDireccion(valor, CampoNombre = 'Dirección') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: 'La dirección es requerida' };
        }
        
        valor = valor.trim();
        
        if (valor.length < 5) {
            return { valido: false, mensaje: 'La dirección debe tener al menos 5 caracteres' };
        }
        
        if (valor.length > 200) {
            return { valido: false, mensaje: 'La dirección no puede tener más de 200 caracteres' };
        }
        
        const palabras = valor.split(/\s+/);
        if (palabras.length < 2) {
            return { valido: false, mensaje: 'La dirección debe incluir calle y número al menos' };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida formato de teléfono
     */
    validarTelefono(valor, campoNombre = 'Teléfono') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: 'El teléfono es requerido' };
        }
        
        valor = valor.trim().replace(/[\s-]/g, '');
        
        if (!/^\d+$/.test(valor)) {
            return { valido: false, mensaje: 'El teléfono solo debe contener números' };
        }
        
        if (valor.length < 7) {
            return { valido: false, mensaje: 'El teléfono debe tener al menos 7 dígitos' };
        }
        
        if (valor.length > 15) {
            return { valido: false, mensaje: 'El teléfono no puede tener más de 15 dígitos' };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida formato de email
     */
    validarEmail(valor, campoNombre = 'Correo electrónico') {
        if (!valor || valor.trim() === '') {
            return { valido: true, mensaje: '' }; // Email opcional
        }
        
        valor = valor.trim();
        
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!pattern.test(valor)) {
            return { valido: false, mensaje: 'El formato del correo electrónico no es válido' };
        }
        
        if (valor.length > 100) {
            return { valido: false, mensaje: 'El correo electrónico no puede tener más de 100 caracteres' };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida que un campo no esté vacío
     */
    validarRequerido(valor, campoNombre = 'Campo') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: `${campoNombre} es requerido` };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida longitud mínima
     */
    validarLongitudMinima(valor, minimo, campoNombre = 'Campo') {
        if (!valor || valor.trim() === '') {
            return { valido: true, mensaje: '' }; // No validar si está vacío
        }
        
        if (valor.length < minimo) {
            return { valido: false, mensaje: `${campoNombre} debe tener al menos ${minimo} caracteres` };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida longitud máxima
     */
    validarLongitudMaxima(valor, maximo, campoNombre = 'Campo') {
        if (valor && valor.length > maximo) {
            return { valido: false, mensaje: `${campoNombre} no puede tener más de ${maximo} caracteres` };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida formato de nombre (solo letras y espacios)
     */
    validarNombre(valor, campoNombre = 'Nombre') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: `${campoNombre} es requerido` };
        }
        
        valor = valor.trim();
        
        if (valor.length < 2) {
            return { valido: false, mensaje: `${campoNombre} debe tener al menos 2 caracteres` };
        }
        
        if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$/.test(valor)) {
            return { valido: false, mensaje: `${campoNombre} solo debe contener letras y espacios` };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    /**
     * Valida formato numérico
     */
    validarNumerico(valor, campoNombre = 'Campo') {
        if (!valor || valor.trim() === '') {
            return { valido: false, mensaje: `${campoNombre} es requerido` };
        }
        
        valor = valor.trim();
        
        if (!/^\d+$/.test(valor)) {
            return { valido: false, mensaje: `${campoNombre} solo debe contener números` };
        }
        
        return { valido: true, mensaje: '' };
    },
    
    // ============================================================================
    // FUNCIONES DE UI PARA MOSTRAR ERRORES
    // ============================================================================
    
    /**
     * Muestra error en un campo
     */
    mostrarError(input, mensaje) {
        const formGroup = input.closest('.form-group') || input.parentElement;
        
        // Remover error existente si hay
        this.ocultarError(input);
        
        // Agregar clase de error
        input.classList.add('input-error');
        input.style.borderColor = '#ef4444';
        
        // Crear elemento de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error';
        errorDiv.style.cssText = 'color: #ef4444; font-size: 12px; margin-top: 4px;';
        errorDiv.textContent = mensaje;
        
        formGroup.appendChild(errorDiv);
    },
    
    /**
     * Oculta error de un campo
     */
    ocultarError(input) {
        input.classList.remove('input-error');
        input.style.borderColor = '';
        
        const formGroup = input.closest('.form-group') || input.parentElement;
        const errorDiv = formGroup.querySelector('.validation-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    },
    
    /**
     * Valida y muestra errores automáticamente
     */
    validarYMostrar(input, validacionFunc, campoNombre) {
        const valor = input.value;
        const resultado = validacionFunc(valor, campoNombre);
        
        if (resultado.valido) {
            this.ocultarError(input);
            input.style.borderColor = '#10b981'; // Verde para válido
        } else {
            this.mostrarError(input, resultado.mensaje);
        }
        
        return resultado;
    },
    
    // ============================================================================
    // GENERADORES AUTOMÁTICOS
    // ============================================================================
    
    /**
     * Genera username basado en nombre completo
     */
    generarUsername(primerNombre, segundoNombre = '', primerApellido = '', segundoApellido = '') {
        const limpiar = (texto) => {
            if (!texto) return '';
            return texto.toLowerCase().trim()
                .replace(/\s/g, '')
                .replace(/[^a-záéíóúñ]/g, '')
                .replace(/á/g, 'a').replace(/é/g, 'e').replace(/í/g, 'i')
                .replace(/ó/g, 'o').replace(/ú/g, 'u');
        };
        
        primerNombre = limpiar(primerNombre);
        segundoNombre = limpiar(segundoNombre);
        primerApellido = limpiar(primerApellido);
        segundoApellido = limpiar(segundoApellido);
        
        let username = primerApellido ? 
            (primerNombre ? primerNombre[0] + primerApellido : primerApellido) : 
            primerNombre;
        
        if (segundoApellido) {
            username += segundoApellido[0];
        }
        
        const numero = Math.floor(Math.random() * 900) + 100;
        username = `${username}${numero}`;
        
        return username.substring(0, 30);
    },
    
    /**
     * Genera contraseña segura
     */
    generarPassword(longitud = 10) {
        const mayusculas = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const minusculas = 'abcdefghijklmnopqrstuvwxyz';
        const numeros = '0123456789';
        const especiales = '!@#$%^&*';
        
        let password = '';
        password += mayusculas[Math.floor(Math.random() * mayusculas.length)];
        password += minusculas[Math.floor(Math.random() * minusculas.length)];
        password += numeros[Math.floor(Math.random() * numeros.length)];
        password += especiales[Math.floor(Math.random() * especiales.length)];
        
        const caracteres = mayusculas + minusculas + numeros + especiales;
        for (let i = 4; i < longitud; i++) {
            password += caracteres[Math.floor(Math.random() * caracteres.length)];
        }
        
        return password.split('').sort(() => Math.random() - 0.5).join('');
    }
};

// Hacer disponible globalmente
if (typeof window !== 'undefined') {
    window.ValidacionPVD = ValidacionPVD;
}
