#!/usr/bin/env python
"""
Genera 3000 ciudadanos con datos colombianos realistas.
1500 por PVD Edificio Rafael Arias · 1500 por PVD Colegio Antonio Nariño
"""
import os, sys, django, random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from modulo_puntos.models import Ciudadano, PuntoViveDigital

# ── PVDs ─────────────────────────────────────────────────────────────────────
pvd_rafael = PuntoViveDigital.objects.get(nombre__icontains='Rafael Arias')
pvd_nariño = PuntoViveDigital.objects.get(nombre__icontains='Antonio Nariño')
print(f"PVD 1: {pvd_rafael.nombre} (id={pvd_rafael.pk})")
print(f"PVD 2: {pvd_nariño.nombre} (id={pvd_nariño.pk})")

# ── Datos base colombianos ────────────────────────────────────────────────────
NOMBRES_M = [
    'Juan', 'Carlos', 'Luis', 'Jorge', 'Andrés', 'Miguel', 'Santiago', 'David',
    'Felipe', 'Daniel', 'Alejandro', 'Sebastián', 'Nicolás', 'Camilo', 'Diego',
    'Fernando', 'Eduardo', 'Sergio', 'Rodrigo', 'Gustavo', 'Mauricio', 'Ricardo',
    'Pablo', 'Álvaro', 'Hernán', 'Mario', 'Raúl', 'César', 'Iván', 'Omar',
    'Jaime', 'Julián', 'Javier', 'Cristian', 'Kevin', 'Jhon', 'Brayan',
    'Anderson', 'Esteban', 'Mateo', 'Samuel', 'Tomás', 'Emilio', 'Antonio',
    'Francisco', 'Manuel', 'Roberto', 'Héctor', 'Ignacio', 'Víctor', 'Óscar',
    'Germán', 'Ernesto', 'Alberto', 'Rafael', 'Humberto', 'Arturo', 'Enrique',
    'Jesús', 'William', 'Alexander', 'Giovanny', 'Nelson', 'Harold', 'Fredy',
    'Jhonatan', 'Yeison', 'Maicol', 'Stiven', 'Yesid', 'Fabio', 'Gilberto',
]

NOMBRES_F = [
    'María', 'Ana', 'Claudia', 'Sandra', 'Paola', 'Laura', 'Carolina', 'Adriana',
    'Marcela', 'Diana', 'Natalia', 'Daniela', 'Valentina', 'Luisa', 'Catalina',
    'Sofía', 'Camila', 'Andrea', 'Alejandra', 'Juliana', 'Gloria', 'Martha',
    'Luz', 'Rosa', 'Elena', 'Esperanza', 'Beatriz', 'Isabel', 'Mónica',
    'Patricia', 'Liliana', 'Amparo', 'Nelly', 'Carmen', 'Pilar', 'Lucía',
    'Fernanda', 'Jessica', 'Viviana', 'Stella', 'Yolanda', 'Verónica',
    'Margarita', 'Ángela', 'Lorena', 'Johana', 'Karen', 'Lina', 'Sara',
    'Norma', 'Consuelo', 'Gladys', 'Ruby', 'Olga', 'Nubia', 'Marta',
    'Blanca', 'Flor', 'Yaneth', 'Yanira', 'Leidy', 'Angie', 'Cindy',
    'Lady', 'Yeimi', 'Yesenia', 'Marisol', 'Fabiola', 'Elsa', 'Teresa',
]

SEGUNDOS_NOMBRES_M = [
    'Alberto', 'Andrés', 'Antonio', 'Arturo', 'Augusto', 'Camilo', 'Carlos',
    'Daniel', 'David', 'Eduardo', 'Emilio', 'Ernesto', 'Felipe', 'Fernando',
    'Francisco', 'Gustavo', 'Hernán', 'Ignacio', 'Javier', 'Jorge', 'José',
    'Juan', 'Julián', 'Luis', 'Manuel', 'Mario', 'Mauricio', 'Miguel',
    'Nelson', 'Nicolás', 'Orlando', 'Pablo', 'Pedro', 'Rafael', 'Ramón',
    'Ricardo', 'Roberto', 'Rodrigo', 'Santiago', 'Sergio', 'Tomás', 'Vicente',
]

SEGUNDOS_NOMBRES_F = [
    'Alejandra', 'Amparo', 'Ana', 'Andrea', 'Beatriz', 'Camila', 'Carolina',
    'Catalina', 'Cecilia', 'Claudia', 'Consuelo', 'Cristina', 'Diana', 'Elena',
    'Esperanza', 'Fernanda', 'Gladys', 'Gloria', 'Helena', 'Inés', 'Isabel',
    'Janeth', 'Juliana', 'Laura', 'Liliana', 'Lorena', 'Lucía', 'Luisa',
    'Marcela', 'María', 'Milena', 'Mónica', 'Natalia', 'Nelly', 'Norma',
    'Olga', 'Paola', 'Patricia', 'Rosa', 'Sandra', 'Sara', 'Stella',
    'Teresa', 'Valentina', 'Verónica', 'Victoria', 'Viviana', 'Yolanda',
]

APELLIDOS = [
    'García', 'Martínez', 'López', 'González', 'Rodríguez', 'Pérez', 'Sánchez',
    'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Hernández',
    'Moreno', 'Ruiz', 'Jiménez', 'Álvarez', 'Vargas', 'Castro', 'Romero',
    'Suárez', 'Rojas', 'Muñoz', 'Valencia', 'Reyes', 'Giraldo', 'Ospina',
    'Cardona', 'Montoya', 'Ríos', 'Salazar', 'Guerrero', 'Mendoza', 'Cruz',
    'Medina', 'Aguilar', 'Nieto', 'Parra', 'Ortega', 'Mora', 'Acosta',
    'Castaño', 'Zapata', 'Arango', 'Mesa', 'Correa', 'Cano', 'Bedoya',
    'Henao', 'Posada', 'Ocampo', 'Quintero', 'Escobar', 'Londoño', 'Toro',
    'Palacio', 'Aristizábal', 'Vélez', 'Hurtado', 'Tobón', 'Mejía',
    'Cárdenas', 'Fuentes', 'Molina', 'Bermúdez', 'Delgado', 'Ramos', 'Peña',
    'Gálvez', 'Sandoval', 'Gutiérrez', 'Barrera', 'Leal', 'Sierra', 'Serrano',
    'Bernal', 'Ayala', 'Vásquez', 'Ossa', 'Patiño', 'Loaiza', 'Orozco',
    'Franco', 'Gallego', 'Muñetón', 'Pino', 'Naranjo', 'Velásquez', 'Duque',
    'Urrego', 'Caicedo', 'Cifuentes', 'Ángel', 'Calderón', 'Aguirre',
    'Trujillo', 'Soto', 'Lozano', 'Cepeda', 'Fonseca', 'Pineda', 'Castillo',
    'Bonilla', 'Arias', 'Arbeláez', 'Rengifo', 'Buriticá', 'Holguín',
    'Zuleta', 'Jaramillo', 'Muñiz', 'Valderrama', 'Pulido', 'Porras',
    'Useche', 'Vergara', 'Zabala', 'Tafur', 'Marín', 'Rincón', 'Garzón',
]

BARRIOS_BUGALAGRANDE = [
    'Centro', 'Obrero', 'Municipal', 'La Planta', 'Gualcoche', 'Los Mármoles',
    'Paulus VI', 'Primero de Mayo', 'José Antonio Galán', 'La Esperanza',
    'Cocicoinpa', 'Ricaurte', 'Brisas del Río', 'Cañaveral', 'El Edén',
    'La María', 'La María II Etapa', 'El Jardín', 'Antonio Nariño', 'Ceilán',
    'Chorreras', 'El Guayabo', 'El Overo', 'Galicia', 'Chicoral', 'El Placer',
    'Uribe', 'Paila Arriba', 'Mestizal', 'Ninguno / Área Rural',
]

MUNICIPIOS_VALLE = [
    'Bugalagrande', 'Bugalagrande', 'Bugalagrande', 'Bugalagrande', 'Bugalagrande',
    'Bugalagrande', 'Bugalagrande', 'Bugalagrande',  # 8:1 mayoría Bugalagrande
    'Tuluá', 'Andalucía', 'Zarzal', 'Roldanillo', 'Cartago', 'Sevilla',
    'Guadalajara de Buga', 'Santiago de Cali', 'Palmira', 'Caicedonia',
]

VEREDAS = [
    '', '', '', '',  # mayoría sin vereda
    'El Placer', 'La Moralia', 'San Marcos', 'La Paila', 'El Overo',
    'El Mestizal', 'Chorreras', 'El Chuzo', 'Coloradas', 'Paila Arriba',
    'Santa Lucía', 'Uribe Uribe', 'El Guayabo', 'Potrerillo', 'Ceilán',
]

CALLES = ['Calle', 'Carrera', 'Avenida', 'Diagonal', 'Transversal']
DOMINIOS = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']

TIPO_DOC_PESOS = [
    ('CC',   65),   # cédula de ciudadanía — mayoría adultos
    ('TI',   15),   # tarjeta de identidad — menores
    ('RC',    5),   # registro civil
    ('CE',    5),   # cédula extranjería
    ('PEP',   4),
    ('PPT',   3),
    ('PA',    2),
    ('NUIP',  1),
]
TIPOS_DOC, PESOS_DOC = zip(*TIPO_DOC_PESOS)

GENERO_PESOS     = [('M', 48), ('F', 50), ('O', 2)]
GENEROS, PESOS_G = zip(*GENERO_PESOS)

ETNIA_PESOS = [
    ('Ninguna', 72), ('Afrocolombiano', 15), ('Indígena', 7),
    ('Raizal', 2), ('Palenquero', 1), ('Rrom', 1), ('Otra', 2),
]
ETNIAS, PESOS_E = zip(*ETNIA_PESOS)

EDUCACION_PESOS = [
    ('Ninguno', 3), ('Preescolar', 2), ('Primaria', 15), ('Secundaria', 22),
    ('Media', 20), ('Técnico', 14), ('Tecnólogo', 8), ('Universitario', 10),
    ('Especialización', 4), ('Maestría', 1), ('Doctorado', 1),
]
EDUCACIONES, PESOS_EDU = zip(*EDUCACION_PESOS)

OCUPACION_PESOS = [
    ('Estudiante', 18), ('Empleado', 25), ('Independiente', 22),
    ('Desempleado', 12), ('Hogar', 13), ('Pensionado', 7), ('Otro', 3),
]
OCUPACIONES, PESOS_OC = zip(*OCUPACION_PESOS)

ESTRATO_PESOS = [(1, 25), (2, 40), (3, 25), (4, 7), (5, 2), (6, 1)]
ESTRATOS, PESOS_EST = zip(*ESTRATO_PESOS)

DISCAPACIDADES = [
    'Visual', 'Auditiva', 'Motriz', 'Cognitiva',
    'Psicosocial', 'Múltiple', 'Sordoceguera',
]

# ── Generadores ───────────────────────────────────────────────────────────────
random.seed(42)

def w(seq, pesos):
    return random.choices(seq, weights=pesos, k=1)[0]

def cedula(tipo):
    if tipo == 'CC':
        return str(random.randint(10_000_000, 1_299_999_999))
    if tipo == 'TI':
        return str(random.randint(900_000_000, 999_999_999))
    if tipo == 'RC':
        return str(random.randint(1_000_000, 99_999_999))
    if tipo == 'NUIP':
        return str(random.randint(1_000_000_000, 1_299_999_999))
    return str(random.randint(10_000_000, 999_999_999))

def fecha_nacimiento(tipo_doc):
    hoy = date.today()
    if tipo_doc == 'RC':
        años = random.randint(0, 6)
    elif tipo_doc == 'TI':
        años = random.randint(7, 17)
    elif tipo_doc == 'NUIP':
        años = random.randint(0, 14)
    elif tipo_doc == 'Pensionado':
        años = random.randint(58, 90)
    else:
        años = random.randint(18, 85)
    delta = random.randint(0, 364)
    return hoy - timedelta(days=años * 365 + delta)

def direccion():
    calle  = random.choice(CALLES)
    num1   = random.randint(1, 50)
    num2   = random.randint(1, 99)
    num3   = random.randint(1, 99)
    return f'{calle} {num1} # {num2}-{num3}'

def telefono():
    prefijos = ['300', '301', '302', '303', '304', '305', '310',
                '311', '312', '313', '314', '315', '316', '317',
                '318', '319', '320', '321', '322', '323', '350']
    return random.choice(prefijos) + str(random.randint(1_000_000, 9_999_999))

def correo(nombre, apellido, n):
    nombre_clean  = nombre.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace(' ','')
    apellido_clean= apellido.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace(' ','')
    sep = random.choice(['', '.', '_'])
    sufijo = str(n) if random.random() < 0.4 else ''
    return f'{nombre_clean}{sep}{apellido_clean}{sufijo}@{random.choice(DOMINIOS)}'

# ── Crear ciudadanos ──────────────────────────────────────────────────────────
print(f'\nGenerando 3000 ciudadanos...')
docs_usados = set()
lote = []
TOTAL = 3000
LOTE_SIZE = 200

for i in range(TOTAL):
    pvd = pvd_rafael if i < 1500 else pvd_nariño
    genero = w(GENEROS, PESOS_G)
    tipo_doc = w(TIPOS_DOC, PESOS_DOC)

    # Nombre
    if genero == 'M':
        primer_nombre   = random.choice(NOMBRES_M)
        segundo_nombre  = random.choice(SEGUNDOS_NOMBRES_M) if random.random() > 0.25 else ''
    elif genero == 'F':
        primer_nombre   = random.choice(NOMBRES_F)
        segundo_nombre  = random.choice(SEGUNDOS_NOMBRES_F) if random.random() > 0.25 else ''
    else:
        primer_nombre   = random.choice(NOMBRES_M + NOMBRES_F)
        segundo_nombre  = ''

    primer_apellido  = random.choice(APELLIDOS)
    segundo_apellido = random.choice(APELLIDOS)

    # Documento único
    intentos = 0
    while True:
        doc = cedula(tipo_doc)
        if doc not in docs_usados:
            docs_usados.add(doc)
            break
        intentos += 1
        if intentos > 50:
            doc = doc + str(random.randint(10, 99))
            docs_usados.add(doc)
            break

    fnac      = fecha_nacimiento(tipo_doc)
    municipio = w(MUNICIPIOS_VALLE, [1]*len(MUNICIPIOS_VALLE))
    barrio    = random.choice(BARRIOS_BUGALAGRANDE) if municipio == 'Bugalagrande' else ''
    zona_r    = random.choice(VEREDAS) if barrio in ('Ninguno / Área Rural', '') else ''
    estrato   = str(w(ESTRATOS, PESOS_EST))
    disc      = random.random() < 0.06   # 6% discapacidad
    desc_disc = random.choice(DISCAPACIDADES) if disc else ''

    tiene_correo   = random.random() < 0.55
    tiene_telefono = random.random() < 0.72

    lote.append(Ciudadano(
        punto_vive_digital    = pvd,
        tipo_documento        = tipo_doc,
        numero_documento      = doc,
        primer_nombre         = primer_nombre,
        segundo_nombre        = segundo_nombre,
        primer_apellido       = primer_apellido,
        segundo_apellido      = segundo_apellido,
        fecha_nacimiento      = fnac,
        genero                = genero,
        etnia                 = w(ETNIAS, PESOS_E),
        nivel_educativo       = w(EDUCACIONES, PESOS_EDU),
        ocupacion             = w(OCUPACIONES, PESOS_OC),
        estrato               = estrato,
        direccion             = direccion(),
        municipio             = municipio,
        barrio                = barrio,
        zona_rural            = zona_r,
        correo                = correo(primer_nombre, primer_apellido, i) if tiene_correo else '',
        telefono              = telefono() if tiene_telefono else '',
        tiene_discapacidad    = disc,
        descripcion_discapacidad = desc_disc,
        estado                = 'A',
    ))

    if len(lote) >= LOTE_SIZE:
        Ciudadano.objects.bulk_create(lote, ignore_conflicts=True)
        insertados = (i + 1)
        print(f'  ✓ {insertados:>4} / {TOTAL} ciudadanos insertados...')
        lote = []

if lote:
    Ciudadano.objects.bulk_create(lote, ignore_conflicts=True)

# ── Resumen ───────────────────────────────────────────────────────────────────
total  = Ciudadano.objects.count()
rafael = Ciudadano.objects.filter(punto_vive_digital=pvd_rafael).count()
nariño = Ciudadano.objects.filter(punto_vive_digital=pvd_nariño).count()

print()
print('═'*55)
print('  RESUMEN FINAL')
print('═'*55)
print(f'  Total ciudadanos en BD : {total}')
print(f'  PVD Edificio Rafael Arias : {rafael}')
print(f'  PVD Colegio Antonio Nariño : {nariño}')

# Distribución género
from django.db.models import Count
print()
print('  Distribución por género:')
for g in Ciudadano.objects.values('genero').annotate(n=Count('id')).order_by('-n'):
    label = {'M':'Masculino','F':'Femenino','O':'Otro'}.get(g['genero'], g['genero'])
    print(f'    {label}: {g["n"]}')

print()
print('  Distribución por tipo de documento:')
for t in Ciudadano.objects.values('tipo_documento').annotate(n=Count('id')).order_by('-n'):
    print(f'    {t["tipo_documento"]}: {t["n"]}')

print()
print('  Distribución por ocupación:')
for o in Ciudadano.objects.values('ocupacion').annotate(n=Count('id')).order_by('-n'):
    print(f'    {o["ocupacion"]}: {o["n"]}')

print()
print('  ✅ Ciudadanos creados exitosamente.')
print('═'*55)
