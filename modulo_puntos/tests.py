"""
Pruebas de aislamiento multi-tenant entre Puntos Vive Digital (PVD).

Cubren la regla central del sistema: un Administrador PVD sólo puede ver/editar/
eliminar datos de su propio PVD activo, aunque adivine o incremente un ID en la
URL (IDOR). También cubren que los reportes/exportaciones fallan "cerrado"
(niegan acceso) en vez de "abierto" (mostrar todo) cuando falta el PVD activo
en sesión, y que Superusuario/Admin TIC conservan acceso sin restricción.
"""
from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Atencion, Curso, MantenimientoEquipo, PermisoDefinicion, PermisoRol,
    PrestamoRecurso, PuntoViveDigital, Recurso, Sala, Ciudadano, UserProfile,
)


class AislamientoPvdTestCase(TestCase):
    """Base: dos PVD (A y B), un Admin PVD atado a A, y un objeto de cada
    módulo perteneciente a B, para verificar que A no puede tocarlos."""

    @classmethod
    def setUpTestData(cls):
        cls.pvd_a = PuntoViveDigital.objects.create(nombre='PVD A', estado='A')
        cls.pvd_b = PuntoViveDigital.objects.create(nombre='PVD B', estado='A')

        grupo_pvd = Group.objects.create(name='Administrador PVD')
        grupo_tic = Group.objects.create(name='Administrador TIC')

        cls.admin_pvd_a = User.objects.create_user('admin_a', password='x')
        cls.admin_pvd_a.groups.add(grupo_pvd)
        UserProfile.objects.create(usuario=cls.admin_pvd_a, rol='admin_pvd', punto_asignado=cls.pvd_a)

        cls.admin_tic = User.objects.create_user('admin_tic', password='x')
        cls.admin_tic.groups.add(grupo_tic)

        # Permisos que algunas vistas exigen además del check de PVD (algunos
        # códigos ya vienen sembrados por una migración de datos del sistema).
        for codigo in ('salas.editar', 'cursos.editar', 'mantenimiento.editar'):
            pd, _ = PermisoDefinicion.objects.get_or_create(
                codigo=codigo, defaults={'nombre': codigo, 'categoria': 'test'}
            )
            PermisoRol.objects.get_or_create(rol='admin_pvd', permiso=pd)

        # Un ciudadano y una atención por PVD.
        cls.ciudadano_b = Ciudadano.objects.create(
            punto_vive_digital=cls.pvd_b, tipo_documento='CC', numero_documento='9990001',
            primer_nombre='Foráneo', primer_apellido='DeB', estado='A',
        )
        cls.atencion_b = Atencion.objects.create(
            punto_vive_digital=cls.pvd_b, ciudadano=cls.ciudadano_b, fecha=date(2026, 1, 1), estado='P',
        )
        cls.recurso_b = Recurso.objects.create(punto_vive_digital=cls.pvd_b, tipo='Laptop-B', estado='A')
        cls.prestamo_b = PrestamoRecurso.objects.create(recurso=cls.recurso_b, fecha_entrega='2026-01-01T08:00:00Z')
        cls.sala_b = Sala.objects.create(punto_vive_digital=cls.pvd_b, nombre='Sala B', estado='A')
        cls.curso_b = Curso.objects.create(punto_vive_digital=cls.pvd_b, nombre='Curso B', fecha_inicio=date(2026, 1, 1))
        cls.mant_b = MantenimientoEquipo.objects.create(
            punto_vive_digital=cls.pvd_b, tipo='PRV', fecha=date(2026, 1, 1),
            equipos_intervenidos='PC-1', descripcion='Limpieza',
        )

        # Contraparte en el PVD A, para las pruebas de listados con alcance.
        cls.recurso_a = Recurso.objects.create(punto_vive_digital=cls.pvd_a, tipo='Laptop-A', estado='A')
        cls.prestamo_a = PrestamoRecurso.objects.create(recurso=cls.recurso_a, fecha_entrega='2026-01-01T08:00:00Z')

    def _login_admin_a_con_pvd_activo(self):
        self.client.login(username='admin_a', password='x')
        session = self.client.session
        session['pvd_activo_id'] = self.pvd_a.pk
        session.save()

    def _login_admin_a_sin_pvd_activo(self):
        self.client.login(username='admin_a', password='x')

    def _assert_redirige_y_no_toca_datos(self, response):
        self.assertEqual(response.status_code, 302)


class ObjetosDeOtroPvdTests(AislamientoPvdTestCase):
    """Un Admin PVD del punto A no puede ver/editar/eliminar objetos del punto B."""

    def test_desactivar_ciudadano_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:desactivar_ciudadano', args=[self.ciudadano_b.pk])
        resp = self.client.post(url)
        self._assert_redirige_y_no_toca_datos(resp)
        self.ciudadano_b.refresh_from_db()
        self.assertEqual(self.ciudadano_b.estado, 'A')  # no se tocó

    def test_historial_ciudadano_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:historial_ciudadano', args=[self.ciudadano_b.pk])
        resp = self.client.get(url)
        self._assert_redirige_y_no_toca_datos(resp)

    def test_cambiar_estado_atencion_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:cambiar_estado_atencion', args=[self.atencion_b.pk])
        resp = self.client.post(url, {'estado': 'F'})
        self._assert_redirige_y_no_toca_datos(resp)
        self.atencion_b.refresh_from_db()
        self.assertEqual(self.atencion_b.estado, 'P')  # no se tocó

    def test_editar_recurso_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:editar_recurso', args=[self.recurso_b.pk])
        resp = self.client.get(url)
        self._assert_redirige_y_no_toca_datos(resp)

    def test_editar_sala_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:editar_sala', args=[self.sala_b.pk])
        resp = self.client.get(url)
        self._assert_redirige_y_no_toca_datos(resp)

    def test_editar_curso_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:editar_curso', args=[self.curso_b.pk])
        resp = self.client.get(url)
        self._assert_redirige_y_no_toca_datos(resp)

    def test_eliminar_mantenimiento_de_otro_pvd_es_rechazado(self):
        self._login_admin_a_con_pvd_activo()
        url = reverse('modulo_puntos:eliminar_mantenimiento', args=[self.mant_b.pk])
        resp = self.client.post(url)
        self._assert_redirige_y_no_toca_datos(resp)
        self.assertTrue(MantenimientoEquipo.objects.filter(pk=self.mant_b.pk).exists())  # no se borró


class ListadosConAlcancePorPvdTests(AislamientoPvdTestCase):
    """Los listados "globales" quedan acotados al PVD activo para Admin PVD."""

    def test_consultar_ciudadanos_no_muestra_ciudadanos_de_otro_pvd(self):
        ciudadano_a = Ciudadano.objects.create(
            punto_vive_digital=self.pvd_a, tipo_documento='CC', numero_documento='1110001',
            primer_nombre='Local', primer_apellido='DeA', estado='A',
        )
        self._login_admin_a_con_pvd_activo()
        resp = self.client.get(reverse('modulo_puntos:consultar_ciudadanos'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '1110001')
        self.assertNotContains(resp, '9990001')

    def test_lista_prestamos_global_no_muestra_prestamos_de_otro_pvd(self):
        self._login_admin_a_con_pvd_activo()
        resp = self.client.get(reverse('modulo_puntos:lista_prestamos_global'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Laptop-A')
        self.assertNotContains(resp, 'Laptop-B')


class ReportesYExportacionesFailClosedTests(AislamientoPvdTestCase):
    """Sin PVD activo en sesión, un Admin PVD no puede ver reportes ni exportar
    (antes de la corrección, esto mostraba/exportaba todos los PVD sin filtrar)."""

    def test_reportes_sin_pvd_activo_redirige_a_seleccionar_pvd(self):
        self._login_admin_a_sin_pvd_activo()
        resp = self.client.get(reverse('modulo_puntos:reportes'))
        self.assertRedirects(resp, reverse('modulo_puntos:seleccionar_pvd_view'))

    def test_exportar_ciudadanos_sin_pvd_activo_redirige_a_seleccionar_pvd(self):
        self._login_admin_a_sin_pvd_activo()
        resp = self.client.get(reverse('modulo_puntos:exportar_ciudadanos_csv'))
        self.assertRedirects(resp, reverse('modulo_puntos:seleccionar_pvd_view'))

    def test_reportes_con_pvd_activo_si_funciona(self):
        self._login_admin_a_con_pvd_activo()
        resp = self.client.get(reverse('modulo_puntos:reportes'))
        self.assertEqual(resp.status_code, 200)


class AccesoSinRestriccionParaTicYSuperTests(AislamientoPvdTestCase):
    """Admin TIC / Superusuario no deben quedar bloqueados por el PVD activo."""

    def test_admin_tic_puede_ver_atencion_de_cualquier_pvd(self):
        self.client.login(username='admin_tic', password='x')
        url = reverse('modulo_puntos:cambiar_estado_atencion', args=[self.atencion_b.pk])
        resp = self.client.post(url, {'estado': 'F'})
        # Redirige tras la acción (patrón normal de la vista), pero sí la ejecuta.
        self.assertEqual(resp.status_code, 302)
        self.atencion_b.refresh_from_db()
        self.assertEqual(self.atencion_b.estado, 'F')

    def test_superusuario_puede_ver_reportes_sin_pvd_activo(self):
        su = User.objects.create_superuser('root', 'root@example.com', 'x')
        self.client.login(username='root', password='x')
        resp = self.client.get(reverse('modulo_puntos:reportes'))
        self.assertEqual(resp.status_code, 200)
