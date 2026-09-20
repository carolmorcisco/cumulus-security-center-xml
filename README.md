# Cumulus Security Center para Cisco 9811

Servicio XML para que el botón de emergencia del Cisco Desk Phone 9811 abra una
experiencia visual de asistencia inmediata. El usuario selecciona la alerta y
puede conectar la llamada con el especialista que atiende en el Cisco 9861.

## Flujo de demostración

1. El usuario presiona el botón rojo del Cisco 9811.
2. El teléfono abre **Cumulus Emergencias**.
3. El usuario selecciona una de estas opciones:
   - Posible fraude.
   - Incidente caja.
   - Desembolso >50K.
   - Alerta oficina.
4. El teléfono muestra **ALERTA DE EMERGENCIA** y una frase claramente
   separada, por ejemplo: **Posible fraude: Conectar con especialista?**
5. El usuario presiona **Conectar**.
6. El 9811 llama a la extensión configurada para el Cisco 9861.

El servicio utiliza el URI compacto \`Dial:<extension>\`. Después de presionar
**Conectar**, el teléfono cambia a su interfaz nativa de llamada. No se generan
códigos de referencia ni se muestran nombres de equipos.

Los textos están abreviados deliberadamente para la pantalla pequeña del 9811.
La interfaz utiliza el menú nativo del teléfono y evita párrafos, imágenes
pesadas y desplazamiento innecesario.

## Prueba local en Mac

```bash
cd cumulus-security-center-xml
python3 -m venv .venv
source .venv/bin/activate
python app.py
```

Abra estas direcciones:

- Preview para navegador: `http://127.0.0.1:8000/preview`
- XML que recibirá el 9811: `http://127.0.0.1:8000/`
- Estado del servicio: `http://127.0.0.1:8000/health`

Para ejecutar las pruebas:

```bash
python -m unittest discover -s tests -v
```

## Publicación en GitHub

1. Cree un repositorio llamado `cumulus-security-center-xml`.
2. Suba todos los archivos de esta carpeta a la raíz del repositorio.
3. Confirme que `.env` no se haya subido.

## Despliegue en Render

1. En Render, seleccione **New + > Blueprint**.
2. Conecte el repositorio `cumulus-security-center-xml`.
3. Render detectará `render.yaml`.
4. Configure `SPECIALIST_EXTENSION` con la extensión real del Cisco 9861.
5. Configure `PUBLIC_BASE_URL` con la URL HTTPS final asignada por Render, sin
   `/` al final. Ejemplo: `https://cumulus-security-center.onrender.com`.
6. Despliegue y abra `/health`; debe devolver `"status":"ok"`.
7. Abra `/preview` para revisar la vista conceptual en un navegador.

## Configuración del Cisco 9811 en Control Hub

1. Vaya a **Devices** y seleccione el Cisco 9811.
2. Abra **All configurations**.
3. Vaya a **Phone > Action Button**.
4. Configure:
   - **Action Button Function:** `Custom`
   - **Action Button Service Name:** `Cumulus Security Center`
   - **Action Button Service Destination:** la URL HTTPS raíz de Render.
   - **Service Trigger:** `Single Press`
   - **Dial Out Delay:** `0`
   - **Silent Emergency Call:** `Disabled`
5. Seleccione **Next > Apply > Close**.
6. Espere a que el teléfono reciba la configuración y haga la prueba.

## Variables

| Variable | Propósito |
| --- | --- |
| `SPECIALIST_EXTENSION` | Extensión Webex Calling del Cisco 9861 receptor. |
| `PUBLIC_BASE_URL` | URL HTTPS pública del servicio XML en Render. |

El valor local predeterminado de `SPECIALIST_EXTENSION` es `7001`; cámbielo por
la extensión real antes de la demostración.

## Compatibilidad

La aplicación utiliza objetos `CiscoIPPhoneMenu` y `CiscoIPPhoneText`, softkeys
personalizadas y el URI interno `Dial:`. La respuesta HTTP se entrega como
`text/xml` con codificación UTF-8 y sin caché.
