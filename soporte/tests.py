from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from .models import Solicitud

URL = '/api/solicitudes/'
CLAVE = 'Clave123'
VALIDA = {
    'titulo': 'Mouse dañado',
    'descripcion': 'El mouse no responde al hacer click',
    'categoria': 'Hardware',
}


class SolicitudAPITests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user('ana', password=CLAVE)
        cls.beto = User.objects.create_user('beto', password=CLAVE)
        cls.admin = User.objects.create_user('admin', password=CLAVE, is_staff=True)
        cls.de_ana = Solicitud.objects.create(
            titulo='Teclado roto', descripcion='Varias teclas no funcionan',
            categoria='Hardware', usuario=cls.ana)
        cls.de_beto = Solicitud.objects.create(
            titulo='Sin internet', descripcion='No hay red en el segundo piso',
            categoria='Redes', usuario=cls.beto)

    # 1
    def test_01_usuario_registra_solicitud_valida(self):
        self.client.force_login(self.ana)
        r = self.client.post(URL, VALIDA, format='json')
        self.assertEqual(r.status_code, 201)
        s = Solicitud.objects.get(pk=r.data['id'])
        self.assertEqual(s.usuario, self.ana)
        self.assertEqual(s.estado, 'Pendiente')

    def test_01b_ignora_usuario_enviado_por_el_cliente(self):
        self.client.force_login(self.ana)
        r = self.client.post(URL, {**VALIDA, 'usuario': self.beto.id}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Solicitud.objects.get(pk=r.data['id']).usuario, self.ana)

    # 2
    def test_02_usuario_lista_solo_sus_solicitudes(self):
        self.client.force_login(self.ana)
        r = self.client.get(URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([s['id'] for s in r.data], [self.de_ana.id])

    # 3
    def test_03_solicitud_ajena_devuelve_404(self):
        self.client.force_login(self.ana)
        r = self.client.get(f'{URL}{self.de_beto.id}/')
        self.assertEqual(r.status_code, 404)

    # 4
    def test_04_usuario_normal_no_cambia_estado(self):
        self.client.force_login(self.ana)
        r = self.client.patch(f'{URL}{self.de_ana.id}/', {'estado': 'Resuelta'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.de_ana.refresh_from_db()
        self.assertEqual(self.de_ana.estado, 'Pendiente')

    # 5
    def test_05_admin_cambia_estado(self):
        self.client.force_login(self.admin)
        r = self.client.patch(f'{URL}{self.de_ana.id}/', {'estado': 'En proceso'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.de_ana.refresh_from_db()
        self.assertEqual(self.de_ana.estado, 'En proceso')

    # 6
    def test_06_datos_invalidos_400(self):
        self.client.force_login(self.ana)
        r = self.client.post(URL, {'titulo': '', 'descripcion': 'x', 'categoria': 'Otra'}, format='json')
        self.assertEqual(r.status_code, 400)

    # 7
    def test_07_admin_elimina_solicitud(self):
        self.client.force_login(self.admin)
        r = self.client.delete(f'{URL}{self.de_ana.id}/')
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Solicitud.objects.filter(pk=self.de_ana.id).exists())

    def test_07b_usuario_normal_no_puede_eliminar(self):
        self.client.force_login(self.ana)
        r = self.client.delete(f'{URL}{self.de_ana.id}/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Solicitud.objects.filter(pk=self.de_ana.id).exists())

    # 8
    def test_08_sin_autenticacion_rechazado(self):
        r = self.client.get(URL)
        self.assertIn(r.status_code, (401, 403))

    # 9: login real, logout real y reutilización
    def test_09_logout_invalida_la_sesion(self):
        r = self.client.post('/api-auth/login/', {'username': 'ana', 'password': CLAVE})
        self.assertEqual(r.status_code, 302)              # login correcto: redirige
        self.assertEqual(self.client.get(URL).status_code, 200)
        self.client.post('/api-auth/logout/')
        self.assertIn(self.client.get(URL).status_code, (401, 403))

    def test_09b_login_con_clave_incorrecta_no_crea_sesion(self):
        self.client.post('/api-auth/login/', {'username': 'ana', 'password': 'incorrecta'})
        self.assertIn(self.client.get(URL).status_code, (401, 403))

    # 10
    def test_10_escritura_sin_csrf_es_rechazada(self):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.ana)
        r = cliente.post(URL, VALIDA, format='json')
        self.assertEqual(r.status_code, 403)

    def test_10b_escritura_con_csrf_valido_funciona(self):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.ana)
        cliente.get('/api-auth/login/')                    # esta página entrega la cookie csrftoken
        token = cliente.cookies['csrftoken'].value
        r = cliente.post(URL, VALIDA, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 201)