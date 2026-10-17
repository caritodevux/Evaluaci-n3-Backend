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

Con el entorno virtual activo, crear el super ususrio y dos usuarios normales en desde `http://127.0.0.1:8000/admin/` (sin marcar "Staff status"):
- admin `python manage.py createsuperuser`
- ana
- beto

Alternativamente se puede usar una vez:
`python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@ejemplo.cl', 'admin'); User.objects.create_user('ana', password='Clave123'); User.objects.create_user('beto', password='Clave123')"`

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
├── db.sqlite3
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
