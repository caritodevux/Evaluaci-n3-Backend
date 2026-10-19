# API de Solicitudes de Soporte Técnico
Evaluación Práctica N.º 3: API RESTful con Django REST Framework (sesiones, CSRF y permisos por perfil).

## 1. Tecnologías
Python 3, Django, Django REST Framework y SQLite (base de datos por defecto de Django).

## 2. Instalación y ejecución
```bash
# 1) Entrar a la carpeta del proyecto (la que contiene manage.py)
python -m venv venv

# 2) Activar el entorno virtual
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac / Linux

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Crear las tablas en SQLite
python manage.py migrate

# 5) Ejecutar el servidor
python manage.py runserver
```

La API queda en `http://127.0.0.1:8000/api/solicitudes/`.

## 3. Usuarios de prueba
Con el entorno virtual activo, es necesario crear un superusuario y dos usuarios estándar (asegurándose de que estos últimos no tengan marcado el permiso "Staff status"). Puedes hacerlo de dos maneras:

**Opción 1: Creación manual**
1. Crea el administrador desde la terminal: `python manage.py createsuperuser`
2. Inicia el servidor e ingresa al panel de administración en `http://127.0.0.1:8000/admin/`
3. Crea a los usuarios ana y beto desde la interfaz web.

**Opción 2: Creación automatizada**
Para crear los tres usuarios en un solo paso y con las credenciales exactas, ejecuta el siguiente comando en tu terminal:
`python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@ejemplo.cl', 'admin'); User.objects.create_user('ana', password='Clave123'); User.objects.create_user('beto', password='Clave123')"`

**Resumen de credenciales**
| Usuario | Contraseña | Perfil |
|---|---|---|
| admin | admin | Administrador (`is_staff = True`) |
| ana | Clave123 | Usuario normal |
| beto | Clave123 | Usuario normal |

La colección de Postman usa estas credenciales (variables `pass_admin` y `pass_usuario` de la colección). Si se crean los usuarios con otras contraseñas, hay que editar esas variables antes de ejecutarla.

## 4. Endpoints
| Método | Endpoint | Funcionalidad |
|---|---|---|
| GET | `/api/solicitudes/` | Listar solicitudes |
| GET | `/api/solicitudes/{id}/` | Consultar una solicitud |
| POST | `/api/solicitudes/` | Registrar una solicitud |
| PUT | `/api/solicitudes/{id}/` | Actualizar una solicitud |
| PATCH | `/api/solicitudes/{id}/` | Actualizar campos específicos |
| DELETE | `/api/solicitudes/{id}/` | Eliminar una solicitud |
| GET / POST | `/api-auth/login/` | Iniciar sesión (formulario de Django REST Framework) |
| POST | `/api-auth/logout/` | Cerrar sesión |

Ejemplo de cuerpo para crear una solicitud:

```json
{
  "titulo": "Mouse dañado",
  "descripcion": "El mouse no responde al hacer click",
  "categoria": "Hardware"
}
```

Categorías permitidas: `Hardware`, `Software`, `Redes`.
Estados permitidos: `Pendiente` (valor inicial), `En proceso`, `Resuelta`.

## 5. Autenticación, sesiones y CSRF
- Se usa `SessionAuthentication`: al iniciar sesión Django crea una sesión y entrega la cookie `sessionid`, que el cliente envía en cada petición.
- Todas las vistas exigen sesión (`IsAuthenticated` por defecto en `settings.py`). Sin sesión la API responde **403 Forbidden** (comportamiento de `SessionAuthentication`, aceptado por la guía).
- Al cerrar sesión, Django destruye la sesión en el servidor: reutilizar la cookie anterior ya no funciona.
- Las escrituras (POST, PUT, PATCH, DELETE) con sesión exigen el token CSRF en el header `X-CSRFToken`. Sin token válido la API responde **403**. La interfaz navegable de DRF lo envía automáticamente.

## 6. Permisos por perfil

| Acción | Usuario normal | Administrador (`is_staff`) |
|---|---|---|
| Ver solicitudes | Solo las propias | Todas |
| Consultar una ajena | 404 (no se revela que existe) | Permitido |
| Registrar | Sí (estado siempre "Pendiente") | Sí |
| Modificar título, descripción, categoría | Solo en las propias | En cualquiera |
| Cambiar el estado | **No** (403) | Sí |
| Eliminar | **No** (403) | Sí (204) |

`usuario` y `fecha_creacion` los asigna el servidor y no se pueden modificar desde el cliente.
Los permisos se comprueban en el servidor (`views.py`), no solo se oculta información.

## 7. Pruebas de funcionamiento

### 7.1 Pruebas automáticas
```bash
python manage.py test
```
Cubren los 10 escenarios de la evaluación (archivo `soporte/tests.py`).

### 7.2 Colección de Postman
1. Importar `postman_collection.json` en Postman.
2. Con el servidor en marcha y los usuarios de prueba creados, ejecutar la colección completa con **Collection Runner**, **en orden**.
3. Mantener activada la opción *Automatically follow redirects* (el login y el logout de Django responden con una redirección).
4. Usar siempre `127.0.0.1` (no mezclar con `localhost`) para que Postman conserve las cookies.
5. **Ejecutar siempre la colección completa, desde la primera request ("00")**: cada request toma el token CSRF y los ids de la anterior, por lo que una request suelta puede responder 403.
6. Resultado esperado: 25 requests y 29 pruebas pasadas, sin errores.

### 7.3 Interfaz navegable de DRF
1. Abrir `http://127.0.0.1:8000/api-auth/login/` e iniciar sesión.
2. Usar `http://127.0.0.1:8000/api/solicitudes/` (formularios POST, PUT, PATCH, DELETE).
3. Cerrar sesión desde el menú del usuario (esquina superior derecha).

### 7.4 Escenarios exigidos

| N.º | Escenario | Resultado esperado | Cómo verlo |
|---|---|---|---|
| 1 | Usuario autenticado registra solicitud válida | 201 Created | Postman "E1" · test `test_01` |
| 2 | Usuario consulta sus solicitudes | 200 OK | "E2" · `test_02` |
| 3 | Usuario consulta solicitud ajena | 404 | "E3" · `test_03` |
| 4 | Usuario normal intenta cambiar el estado | 403 (rechazada) | "E4" · `test_04` |
| 5 | Administrador cambia el estado | 200 OK | "E5" · `test_05` |
| 6 | Usuario envía datos inválidos | 400 Bad Request | "E6" · `test_06` |
| 7 | Administrador elimina una solicitud | 204 No Content | "E7" · `test_07` |
| 8 | Cliente sin autenticación accede a la API | 403 (rechazado) | "E8/E9b" · `test_08` |
| 9 | Usuario cierra sesión e intenta reutilizarla | 403 (rechazado) | "E9a/E9b" · `test_09` |
| 10 | Escritura por sesión sin token CSRF válido | 403 (rechazada) | "E10" · `test_10` |

Comprobación manual del escenario 10 (con sesión iniciada en el navegador, en la consola de DevTools):

```js
// Sin token CSRF -> debe responder 403
fetch('/api/solicitudes/', {method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({titulo: 'Prueba CSRF', descripcion: 'Sin token en el header', categoria: 'Redes'})
}).then(r => console.log(r.status));

// Con token CSRF -> debe responder 201
fetch('/api/solicitudes/', {method: 'POST',
  headers: {'Content-Type': 'application/json',
            'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1]},
  body: JSON.stringify({titulo: 'Prueba CSRF', descripcion: 'Con token en el header', categoria: 'Redes'})
}).then(r => console.log(r.status));
```
### 7.5 Independencia de los usuarios de prueba
**Qué no depende de los usuarios**
- **La API** (`views.py`, `serializers.py`). Decide por `is_staff`, no por el nombre: cualquier usuario con `is_staff=True` funciona como administrador y cualquier otro como usuario normal. El nombre de usuario solo se usa para mostrarlo en las respuestas.
- **`python manage.py test`.** Los tests crean sus propios usuarios (`ana`, `beto` y `admin`) en una base de datos temporal que Django crea y destruye en cada ejecución. No tocan la base de datos del proyecto, por lo que dan el mismo resultado aunque existan otros usuarios, o incluso otros llamados `ana` o `admin`.

**Qué sí depende de los usuarios**
- **La colección de Postman** inicia sesión con los nombres `admin`, `ana` y `beto` (sección 3). Las contraseñas están en las variables de la colección `pass_admin` y `pass_usuario`, pero los nombres están fijos en las requests de login (`01 Login beto`, `04 Login ana` y `05 Login admin`), y las pruebas "E1" y "E2" comparan con el usuario `ana`. Si se usan otros nombres, hay que editar esas requests y esas dos pruebas antes de ejecutarla.

### 7.6 Trazabilidad: de cada prueba al código
Cada prueba de la colección de Postman (y su equivalente en `soporte/tests.py`) se explica por una parte concreta del código:

| Prueba | Dónde se resuelve | Qué ocurre |
|---|---|---|
| **E1** Registrar solicitud válida (201) | `serializers.py` y `perform_create` en `views.py` | Si el serializer es válido, `perform_create` guarda con `usuario=request.user`. El estado "Pendiente" proviene del `default` del modelo |
| **E2** Listar solicitudes (200, solo las propias) | `get_queryset` en `views.py` | El usuario normal recibe `filter(usuario=request.user)` |
| **E3** Consultar solicitud ajena (404) | `get_queryset` en `views.py` | DRF busca el objeto dentro del queryset ya filtrado; si no está, responde 404 sin revelar que existe |
| **E4** Usuario normal cambia el estado (403) | `perform_update` en `views.py` | Si no es `is_staff` y el estado nuevo es distinto del actual, lanza `PermissionDenied` |
| **E5** Administrador cambia el estado (200) | `get_queryset` y `perform_update` | El administrador ve todas las solicitudes y `perform_update` lo permite |
| **E6** Datos inválidos (400) | `validate_titulo` y `validate_descripcion` en `serializers.py`, más los `choices` del modelo | El serializer falla antes de llegar a `perform_create` y DRF responde 400 |
| **E7** Administrador elimina (204) | `perform_destroy` en `views.py` | Si es `is_staff`, ejecuta `instance.delete()` |
| Usuario normal intenta eliminar (403) | `perform_destroy` en `views.py` | Lanza `PermissionDenied` (si la solicitud fuera ajena, antes respondería 404) |
| `usuario` enviado por el cliente se ignora | `serializers.py` | `ReadOnlyField` y `read_only_fields` impiden que el valor llegue a `validated_data` |

Observación sobre el orden de las validaciones: en E4 el serializer comprueba primero que el estado enviado sea uno de los permitidos y después `perform_update` rechaza el cambio por falta de permisos. Si se enviara un estado inexistente, la respuesta sería 400 y no 403.

Las pruebas **E8, E9 y E10** no dependen de `views.py` ni de `serializers.py`, sino de la configuración de autenticación:

| Prueba | Dónde se resuelve |
|---|---|
| **E8** Acceso sin autenticación (403) | `DEFAULT_PERMISSION_CLASSES = IsAuthenticated` en `settings.py` |
| **E9** Cerrar sesión y reutilizarla (403) | `LogoutView` de Django, disponible por `api-auth/` en `config/urls.py`: destruye la sesión en el servidor y, desde ese momento, aplica lo mismo que en E8 |
| **E10** Escritura sin token CSRF (403) | `SessionAuthentication` de DRF, configurada en `settings.py`: valida el token CSRF en las escrituras |

#### Comprobación del serializer sin servidor

Con el entorno virtual activo, desde `python manage.py shell` (no escribe en la base de datos mientras no se llame a `.save()`):

```python
from soporte.serializers import SolicitudSerializer

# Equivale a E6: datos inválidos
s = SolicitudSerializer(data={'titulo': '', 'descripcion': 'x', 'categoria': 'Otra'})
print(s.is_valid())      # False
print(s.errors)          # un error por cada campo inválido

# Campos protegidos: 'usuario' e 'id' enviados por el cliente se ignoran
s = SolicitudSerializer(data={
    'titulo': 'Mouse dañado',
    'descripcion': 'El mouse no responde al hacer click',
    'categoria': 'Hardware',
    'usuario': 999, 'id': 999,
})
print(s.is_valid())            # True
print(dict(s.validated_data))  # solo titulo, descripcion y categoria
```

## 8. Registro del uso de Inteligencia Artificial

**Herramienta utilizada:** Claude, Gemini

**Consulta realizada:**

> Analiza esta API REST desarrollada con Django REST Framework (se adjunta el código de models.py, serializers.py, views.py, urls.py y settings.py). Revisa específicamente autenticación por sesión, autorización por perfil (usuario normal vs administrador), validación de datos y CSRF. No modifiques el código inicialmente. Primero identifica los problemas encontrados, explica por qué son problemas y luego propón una posible mejora para cada uno.

**Recomendaciones seleccionadas y cómo se aplicaron:**

1. **Control de acceso en el servidor y aislamiento por propietario (evita acceder a datos ajenos cambiando el id en la URL, conocido como IDOR).**
   - *Implementación:* `get_queryset()` en `soporte/views.py` devuelve solo las solicitudes del usuario autenticado (todas si `is_staff`). Además `perform_update` y `perform_destroy` lanzan `PermissionDenied` para acciones reservadas al administrador (cambiar el estado y eliminar).
   - *Verificación:* escenarios 3, 4 y 7 (`test_03`, `test_04`, `test_07` y `test_07b`).

2. **No confiar en los datos enviados por el cliente (mass assignment) y validar entradas.**
   - *Implementación:* en `soporte/serializers.py` los campos `id` y `fecha_creacion` son `read_only` y `usuario` se expone solo como lectura; el propietario se asigna en el servidor con `serializer.save(usuario=request.user)`. Las opciones de `categoria` y `estado` están limitadas con `choices`, y `titulo` y `descripcion` tienen validaciones de largo mínimo.
   - *Verificación:* escenario 6 y `test_01b` (enviar `"usuario": <otro id>` se ignora).

3. **Protección CSRF y cookies de sesión seguras.**
   - *Implementación:* `SessionAuthentication` exige el token CSRF en escrituras. En `settings.py` se fijaron `SESSION_COOKIE_HTTPONLY = True` y `SameSite = 'Lax'` para las cookies de sesión y CSRF. En producción además se debe usar HTTPS.
   - *Verificación:* escenario 10 (`test_10` y `test_10b`).

**Criterio aplicado**: las recomendaciones no se copiaron automáticamente: se revisaron, se comprobaron y se validaron con pruebas antes de dejarlas en el proyecto.

## 9. Estructura del proyecto

```
Evaluación3-Backend/
├── manage.py
├── requirements.txt
├── README.md
├── postman_collection.json
├── db.sqlite3 (se crea al ejecutar `migrate`; no se incluye en la entrega)
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── soporte/
    ├── migrations/
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    └── tests.py
```
