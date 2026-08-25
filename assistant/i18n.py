"""UI translation — a simple key -> text dictionary per language, no
gettext/.po so it can be hand-edited without extra tooling.

Deliberate scope (decided with the user, 2026-08-24): the UI ONLY
(buttons, labels, dialogs). WhatsApp message CONTENT and the S-89 slip
are NOT translated here — each congregation edits those texts
themselves in their own language (already editable from the GUI), and
the S-89 slip is an official form each one brings in their own
language. The UI language is chosen during first-time setup and can be
changed afterwards from General settings (applies on restart, same as
the theme).

Two things that DO follow the UI language even though message content
doesn't (added 2026-08-24, after a real bug was found where every
runtime error was hardcoded in Spanish regardless of language):
1. Every error message the app can show (`errores.*` below) — these are
   app-generated text, not congregation-written content, so they belong
   here like any other UI string. `padlet.py`, `parse_workbook.py`,
   `reminder_workbook.py` and `whatsapp_send.py` import `t` from this
   module directly, same as any GUI file.
2. The message-template placeholders (`{nombre}`/`{name}`, etc.) are
   readable in EITHER language no matter which one a congregation's
   `message.txt` happens to use — `whatsapp_send.format_message()` and
   `send_reminders.format_reminder_message()` populate both spellings
   for every field (same pattern as config.py's legacy-key migration).
   Only the *legend* shown in the message editor (`mensaje.ayuda*`) and
   the starter text pre-filled into a brand-new template
   (`mensaje.plantilla_defecto*`) switch with the UI language — an
   already-written `message.txt` is never touched or auto-translated.
"""
from __future__ import annotations

DEFAULT_LANGUAGE = "es"
AVAILABLE_LANGUAGES = {"es": "Español", "en": "English"}

_current_language = DEFAULT_LANGUAGE


def set_language(code: str) -> None:
    global _current_language
    _current_language = code if code in AVAILABLE_LANGUAGES else DEFAULT_LANGUAGE


def current_language() -> str:
    return _current_language


def t(key: str, **kwargs) -> str:
    """Looks up `key` in the current language; if missing, falls back to
    Spanish; if it's not there either, returns the key itself (so an
    untranslated text is visible/searchable instead of crashing or
    showing blank)."""
    text = _TEXTS.get(_current_language, {}).get(key)
    if text is None:
        text = _TEXTS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs) if kwargs else text


_TEXTS: dict[str, dict[str, str]] = {
    "es": {
        # --- General / reused across screens ---
        "app.titulo": "Asistente Vida y Ministerio",
        "comun.guardar": "Guardar",
        "comun.cancelar": "Cancelar",
        "comun.atras": "Atrás",
        "comun.siguiente": "Siguiente",
        "comun.elegir": "Elegir...",

        # --- Initial setup (first-launch notice) ---
        "config_inicial.titulo": "Configuración inicial",
        "config_inicial.mensaje": (
            "Antes de empezar, hay que indicar dónde está el PDF de la S-89 "
            "y otras rutas. Se abrirá la pantalla de configuración."
        ),

        # --- Home ---
        "home.subtitulo_asignaciones": "ASIGNACIONES",
        "home.boton_nueva_asignacion": "Nueva asignación semanal",
        "home.boton_historial": "Historial de envíos",
        "home.boton_mensaje": "Mensaje de asignaciones",
        "home.subtitulo_recordatorios": "RECORDATORIOS VMC",
        "home.boton_nuevo_recordatorio": "Enviar recordatorios",
        "home.boton_historial_recordatorios": "Historial de recordatorios",
        "home.boton_mensaje_recordatorio": "Mensaje de recordatorio",
        "home.subtitulo_comun": "COMÚN",
        "home.boton_contactos": "Contactos",
        "home.boton_config_general": "Configuración general",
        "home.boton_config_avanzada": "Configuración avanzada",

        # --- General settings ---
        "config_general.titulo_ventana": "Configuración general",
        "config_general.ayuda": (
            "Estas rutas se configuran una vez y se usan cada semana. "
            "Cámbialas aquí cuando quieras, sin tocar ningún archivo a mano."
        ),
        "config_general.s89_pdf": "PDF de la S-89:",
        "config_general.s89_pdf_dialogo": "Selecciona el PDF de la S-89",
        "config_general.carpeta_salida": "Carpeta de salida:",
        "config_general.carpeta_salida_dialogo": "Selecciona la carpeta de salida",
        "config_general.abrir_carpeta": "Abrir carpeta de instalación",
        "config_general.rutas_titulo": "Rutas",
        "config_general.padlet_titulo_corto": "Padlet (opcional)",
        "config_general.padlet_url": "URL del tablón:",
        "config_general.padlet_password": "Contraseña:",
        "config_general.padlet_workbook_title": "Título de la publicación VMC:",
        "config_general.drive_titulo_corto": "Google Drive (opcional)",
        "config_general.drive_link": "Enlace para compartir:",
        "config_general.drive_nota": "El archivo debe compartirse con \"Cualquiera con el enlace\".",
        "config_general.preferencias_titulo": "Idioma y tema",
        "config_general.idioma": "Idioma:",
        "config_general.idioma_nota": "El cambio de idioma se aplica al reiniciar la aplicación, igual que el tema.",
        "config_general.tema": "Tema:",
        "config_general.tema_claro": "Claro",
        "config_general.tema_oscuro": "Oscuro",
        "config_general.tema_sistema": "Automático (según el sistema)",
        "config_general.tema_nota": "El cambio de tema se aplica al reiniciar la aplicación.",

        # --- Room labels (models.py) ---
        "room.principal": "Sala principal",
        "room.aux1": "Sala auxiliar 1",
        "room.aux2": "Sala auxiliar 2",

        # --- Wizard steps (widgets.py) ---
        "widgets.paso_de": "PASO {actual} DE {total} — {nombre}",
        "pasos.vmc": "VMC",
        "pasos.semana": "Semana",
        "pasos.revisar": "Revisar",
        "pasos.vista_previa": "Vista previa",
        "pasos.confirmar": "Confirmar",

        # --- Reused across screens ---
        "comun.cerrar": "Cerrar",
        "comun.cerrar_sin_guardar": "Cerrar sin guardar",
        "comun.probar_conmigo": "Probar conmigo",
        "comun.tu_telefono": "Tu teléfono:",
        "comun.ejemplo_telefono": "código de país + número, sin espacios ni «+»",
        "comun.enviar_prueba": "Enviar prueba",
        "comun.telefono_no_valido_titulo": "Teléfono no válido",
        "comun.telefono_no_valido_msg": "El teléfono debe contener solo números, con prefijo de país (sin '+' ni espacios).",
        "comun.nuevo_contacto_titulo": "Nuevo contacto",
        "comun.telefono_para": "Teléfono para {nombre} (código de país + número, sin '+' ni espacios):",
        "comun.anadir_contacto_tooltip": "Añadir esta persona a la lista de contactos con su teléfono",
        "comun.usar_sugerencia": "Usar {nombre}",
        "comun.usar_sugerencia_tooltip": "¿Es la misma persona que {nombre!r} de la lista de contactos?",
        "comun.abriendo_whatsapp": "Abriendo WhatsApp Web...",
        "comun.escanea_qr": "Escanea el código QR con WhatsApp en tu móvil (Ajustes > Dispositivos vinculados)...",
        "comun.cancelar_envio": "Cancelar",
        "comun.reintentar_fallidos": "Reintentar fallidos",
        "comun.reintentar_fallidos_n": "Reintentar fallidos ({n})",
        "comun.volver_inicio": "Volver al inicio",
        "comun.cancelando": "Cancelando tras el envío actual...",
        "comun.error_enviar_titulo": "Error al enviar",
        "comun.enviado_n": "Enviado {i}/{total}",
        "comun.prueba_enviada": "Prueba enviada. Revisa tu WhatsApp.",
        "comun.prueba_fallo": "No se pudo enviar: {motivo}",
        "comun.error_desconocido": "error desconocido",
        "comun.error_enviar_prueba_titulo": "Error al enviar la prueba",
        "comun.guardado_titulo": "Guardado",
        "comun.no_se_pudo_enviar": "no se pudo enviar",

        # --- VMC picker (assignments and reminders) ---
        "workbook_picker.titulo": "Selecciona el archivo VMC",
        "workbook_picker.ayuda_asignaciones": (
            "El VMC es el PDF con el programa de la reunión (Vida y Ministerio "
            "Cristiano) del que se sacan los nombres, fechas y asignaciones."
        ),
        "workbook_picker.ayuda_recordatorio": (
            "El VMC es el PDF con el programa de la reunión (Vida y Ministerio "
            "Cristiano). Se leerán todos los que participan esa semana."
        ),
        "workbook_picker.ningun_archivo": "(ningún archivo seleccionado)",
        "workbook_picker.elegir_archivo": "Seleccionar archivo VMC (PDF)",
        "workbook_picker.buscar_padlet": "Buscar en el Padlet",
        "workbook_picker.buscando_padlet": "Buscando en el Padlet...",
        "workbook_picker.descargado_padlet": "{nombre} (descargado del Padlet)",
        "workbook_picker.descargado_padlet_generico": "(descargado del Padlet)",
        "workbook_picker.padlet_falta_titulo": "Falta configurar el Padlet",
        "workbook_picker.padlet_falta_msg": (
            "Todavía no has configurado la URL del tablón de Padlet.\n\n"
            "Ve a Configuración general y rellena la sección \"Padlet\" "
            "(URL, contraseña si el tablón la pide, y el título de la "
            "publicación del VMC)."
        ),
        "workbook_picker.padlet_error_titulo": "No se pudo buscar en el Padlet",
        "workbook_picker.error_leer_titulo": "No se pudo leer el VMC",
        "workbook_picker.dialogo_seleccionar": "Selecciona el VMC",
        "workbook_picker.fuente_archivo_titulo": "Archivo local",
        "workbook_picker.fuente_archivo_desc": "Elegir un PDF de tu ordenador",
        "workbook_picker.fuente_padlet_titulo": "Padlet",
        "workbook_picker.fuente_padlet_desc_configurado": "Tablón configurado en Ajustes",
        "workbook_picker.fuente_padlet_desc_sin_configurar": "Sin configurar — pulsa para añadir el tablón",
        "workbook_picker.fuente_drive_titulo": "Google Drive",
        "workbook_picker.fuente_drive_desc_configurado": "Enlace configurado en Ajustes",
        "workbook_picker.fuente_drive_desc_sin_configurar": "Sin configurar — pulsa para añadir el enlace",
        "workbook_picker.listo": "Listo",
        "workbook_picker.buscando_drive": "Descargando desde Google Drive...",
        "workbook_picker.descargado_drive": "{nombre} (descargado de Drive)",
        "workbook_picker.drive_falta_titulo": "Falta configurar Google Drive",
        "workbook_picker.drive_falta_msg": (
            "Todavía no has configurado el enlace de Google Drive.\n\n"
            "Ve a Configuración general y pega el enlace para compartir del "
            "PDF del VMC (con acceso \"Cualquiera con el enlace\")."
        ),
        "workbook_picker.drive_error_titulo": "No se pudo descargar de Drive",

        # --- Week picker (assignments) ---
        "week_picker.titulo": "Elige la semana (o semanas)",
        "week_picker.ayuda": "Marca las semanas que quieres generar y enviar:",
        "week_picker.mes_siguiente": "Seleccionar mes siguiente",
        "week_picker.mes_siguiente_tag": "mes siguiente",
        "week_picker.n_asignaciones": "{n} asignaciones",
        "week_picker.resumen_semanas": "{n} semana(s) seleccionada(s)",
        "week_picker.resumen_asignaciones": "{n} asignación(es) a generar",
        "week_picker.ninguna_titulo": "Ninguna semana elegida",
        "week_picker.ninguna_msg": "Marca al menos una semana para continuar.",

        # --- Review assignments ---
        "review.titulo": "Revisa las asignaciones",
        "review.ayuda": (
            "Puedes editar el nombre, el ayudante o un teléfono ya puesto haciendo doble clic en la casilla, "
            "y ajustar el ancho de las columnas de texto arrastrando su borde. "
            "Desmarca \"Enviar\" en una fila para excluir a esa persona de esta tanda."
        ),
        "review.col_enviar": "Enviar",
        "review.col_fecha": "Fecha",
        "review.col_num": "Nº",
        "review.col_tipo": "Tipo",
        "review.col_sala": "Sala",
        "review.col_nombre": "Nombre",
        "review.col_ayudante": "Ayudante",
        "review.col_telefono": "Teléfono",
        "review.col_sugerencia": "Sugerencia",  # still used by reminder_review.py's own table
        "review.col_estado": "Estado",
        "review.generar_vista_previa": "Generar vista previa",
        "review.pill_sin_telefono": "Sin tel.",
        "review.pill_enviada_corta": "Enviado",
        "review.pill_enviada": "Enviada el {fecha}",
        "review.pill_ok": "OK",
        "review.aviso_sin_telefono": "{n} persona(s) sin teléfono",
        "review.aviso_duplicado": "{n} asignación(es) que ya se enviaron antes (\"Enviar\" desmarcado)",
        "review.revisalas": ". Revísalas antes de continuar.",
        "review.tooltip_duplicado": (
            "Ya se envió esta asignación el {fecha} — \"Enviar\" se ha desmarcado. "
            "Vuelve a marcarlo si de verdad quieres reenviarla."
        ),

        # --- Preview (assignments) ---
        "preview.titulo": "Vista previa",
        "preview.generando": "Generando documentos...",
        "preview.atras_corregir": "Atrás, corregir algo",
        "preview.todo_correcto": "Todo correcto, continuar",
        "preview.falta_s89_titulo": "Falta el PDF de la S-89",
        "preview.falta_s89_msg": (
            "No se encuentra el archivo de la S-89 configurado. "
            "Ve a Configuración general y selecciónalo."
        ),
        "preview.generando_n": "Generando {i}/{total}: {nombre}...",
        "preview.ayuda": "Revisa las papeletas generadas antes de continuar.",
        "preview.n_papeletas_generadas": "{n} papeletas generadas",
        "preview.sin_telefono": "(sin teléfono)",
        "preview.error_titulo": "Error al generar documentos",

        # --- Confirm send (assignments) ---
        "send_confirm.titulo": "Confirmar envío",
        "send_confirm.pregunta_recordatorio": "¿Qué quieres enviar como recordatorio de calendario?",
        "send_confirm.opcion_ics": "Archivo ICS",
        "send_confirm.opcion_gcal": "Link Google Calendar",
        "send_confirm.opcion_ambos": "Ambos",
        "send_confirm.vista_previa_ejemplo": "Así quedará el mensaje (ejemplo con la primera persona):",
        "send_confirm.revisado": "He revisado las papeletas y confirmo que están bien.",
        "send_confirm.enviar": "Enviar",
        "send_confirm.se_van_a_enviar": "Se van a enviar {n} mensajes por WhatsApp.",
        "send_confirm.error_vista_previa": "(No se ha podido generar la vista previa: {error})",

        # --- Sending (assignments) ---
        "sending.titulo": "Enviando",
        "sending.terminado_n_fallidos": "Envío terminado, {n} fallido(s).",
        "sending.terminado_bien": "Envío terminado, todo bien.",
        "sending.resumen_enviados": "{n} enviado(s)",
        "sending.resumen_fallidos": "{n} fallido(s)",

        # --- Week picker (meeting reminders) ---
        "rec_semana.titulo": "Elige la semana",
        "rec_semana.ayuda": (
            "Elige la semana para la que quieres enviar el recordatorio. "
            "Las que aparecen en amarillo tienen menos participantes de lo esperado — "
            "puede que valga la pena revisar el VMC antes de enviar."
        ),
        "rec_semana.n_participantes": "{n} participantes",
        "rec_semana.semana_actual": "Semana actual",
        "rec_semana.semana_siguiente": "Semana que viene",
        "rec_semana.elige_msg": "Elige una semana para continuar.",
        "rec_semana.incompleta_titulo": "Esta semana parece incompleta",
        "rec_semana.incompleta_continuar": "¿Quieres continuar de todos modos?",
        "rec_semana.pill_incompleta": "Incompleta",

        # --- Review recipients (meeting reminders) ---
        "rec_revisar.titulo": "Revisa los destinatarios",
        "rec_revisar.ayuda": (
            "Puedes editar el nombre o un teléfono ya puesto haciendo doble clic en la casilla. "
            "Desmarca \"Enviar\" en una fila para excluir a esa persona de este recordatorio."
        ),
        "rec_revisar.col_participacion": "Participación",
        "rec_revisar.aviso_duplicado": "{n} recordatorio(s) que ya se enviaron antes (\"Enviar\" desmarcado)",
        "rec_revisar.tooltip_duplicado": (
            "Ya se le envió el recordatorio de esta semana el {fecha} — "
            "\"Enviar\" se ha desmarcado. Vuelve a marcarlo si de verdad quieres reenviarlo."
        ),
        "rec_revisar.continuar": "Continuar",
        "rec_revisar.nadie_titulo": "Nadie seleccionado",
        "rec_revisar.nadie_msg": "Marca \"Enviar\" en al menos una persona.",

        # --- Confirm reminder (crop image + message) ---
        "rec_confirmar.titulo": "Vista previa y confirmación",
        "rec_confirmar.generando_imagen": "Generando la imagen de la semana...",
        "rec_confirmar.se_ve_mal": "¿Se ve mal el recorte? Ajústalo:",
        "rec_confirmar.borde_superior": "Borde superior:",
        "rec_confirmar.borde_inferior": "Borde inferior:",
        "rec_confirmar.mostrar_mas": "Mostrar más",
        "rec_confirmar.mostrar_mas_tooltip": "Ampliar el recorte por este borde",
        "rec_confirmar.recortar_mas": "Recortar más",
        "rec_confirmar.recortar_mas_tooltip": "Reducir el recorte por este borde",
        "rec_confirmar.restablecer": "Restablecer recorte",
        "rec_confirmar.asi_quedara_para": "Así quedará el mensaje para:",
        "rec_confirmar.revisado": "He revisado la imagen y el mensaje, están bien.",
        "rec_confirmar.enviar": "Enviar",
        "rec_confirmar.se_van_a_enviar": "Se van a enviar {n} recordatorios por WhatsApp.",
        "rec_confirmar.error_imagen_titulo": "Error al generar la imagen",

        # --- Sending reminders ---
        "rec_enviando.titulo": "Enviando recordatorios",

        # --- Contacts editor ---
        "contactos.titulo_ventana": "Contactos",
        "contactos.ayuda": (
            "Nombre completo y teléfono con código de país, sin '+' ni espacios. "
            "La lista se ordena sola por nombre. Puedes ajustar el ancho de las columnas."
        ),
        "contactos.buscar_placeholder": "Buscar por nombre...",
        "contactos.col_nombre": "Nombre",
        "contactos.col_telefono": "Teléfono",
        "contactos.anadir": "+ Añadir",
        "contactos.borrar_seleccionado": "Borrar seleccionado",
        "contactos.telefono_invalido_de": "El teléfono de '{nombre}' debe contener solo números (sin '+' ni espacios).",
        "contactos.n_guardados": "{n} contactos guardados.",
        "contactos.n_contactos": "{n} contacto(s)",

        # --- History ---
        "historial.titulo_ventana": "Historial de envíos",
        "historial.titulo_recordatorios": "Historial de recordatorios",
        "historial.ayuda": "Registro de cada mensaje enviado (o que falló) por WhatsApp.",
        "historial.col_cuando": "Enviado el",
        "historial.col_asignacion": "Asignación",
        "historial.col_nombre": "Nombre",
        "historial.col_telefono": "Teléfono",
        "historial.col_estado": "Estado",
        "historial.col_motivo": "Motivo",
        "historial.vacio": "(todavía no se ha enviado nada)",
        "historial.pill_fallido": "Fallido",
        "historial.n_resultados": "{n} envío(s)",

        # --- Message editor ---
        "mensaje.titulo_ventana": "Editar mensaje",
        "mensaje.titulo_ventana_recordatorio": "Editar mensaje de recordatorio",
        "mensaje.ayuda": "Puedes usar estos huecos en el mensaje, se rellenan solos:\n{nombre}  {ayudante}  {fecha}  {numero}  {tipo}  {link}",
        "mensaje.ayuda_recordatorio": (
            "Puedes usar estos huecos en el mensaje, se rellenan solos:\n"
            "{nombre}  {nombre_pila}  {rol}  {fecha}  {fecha_relativa}\n"
            "{fecha_relativa} se calcula solo según cuándo envíes el recordatorio "
            "(\"mañana\", \"pasado mañana\", \"la semana que viene\"...)."
        ),
        "mensaje.guardado_msg": "Mensaje guardado.",
        "mensaje.vista_previa": "Vista previa",
        "mensaje.plantilla_defecto": (
            "Buenas {nombre_pila}, te recuerdo que tienes una asignación programada "
            "para el próximo día {fecha}. Puedes añadir este evento a tu calendario "
            "pulsando en el enlace o abriendo el archivo de abajo. Un saludo.\n\n{link}"
        ),
        "mensaje.plantilla_defecto_recordatorio": (
            "¡Muy buenos días {nombre_pila}! Solo recordarte que {fecha_relativa} "
            "tienes participación en la reunión: {rol}. ¡Muchas gracias!"
        ),

        # --- Advanced settings (timing) ---
        "tiempos.titulo_ventana": "Configuración avanzada — tiempos de WhatsApp",
        "tiempos.ayuda": (
            "Tiempos de espera (en segundos) entre cada paso al enviar por WhatsApp. "
            "Valores más altos son más lentos pero más seguros para la cuenta."
        ),
        "tiempos.espera_abrir_chat": "Espera al abrir el chat",
        "tiempos.espera_tras_adjuntar": "Espera tras adjuntar un archivo",
        "tiempos.espera_tras_cargar": "Espera a que el archivo termine de cargar",
        "tiempos.espera_tras_enviar": "Espera tras pulsar enviar",
        "tiempos.pausa_entre_contactos": "Pausa entre cada contacto",
        "tiempos.restaurar_defecto": "Restaurar valores por defecto",

        # --- Try it with me ---
        "test_send.titulo_ventana": "Probar conmigo",
        "test_send.ayuda_asignacion": (
            "Se enviará la papeleta de {nombre} a tu propio número, "
            "para que compruebes cómo queda antes del envío real."
        ),
        "test_send.ayuda_recordatorio": (
            "Se enviará el recordatorio de {nombre} a tu propio número, "
            "para que compruebes cómo queda antes del envío real."
        ),

        # --- Runtime errors (padlet.py, parse_workbook.py,
        # reminder_workbook.py, whatsapp_send.py, gui/workers.py) ---
        "errores.plantilla_no_encontrada": (
            "No se encuentra {ruta}. Créala con el texto del mensaje — abre "
            "\"Mensaje de asignaciones\" o \"Mensaje de recordatorio\" desde "
            "la app para ver los huecos disponibles y guardarla."
        ),
        "errores.sin_navegador": (
            "No se ha podido abrir ningún navegador Chromium/Chrome/Edge. "
            "Instala Google Chrome, usa Microsoft Edge (viene con Windows), "
            "instala Chromium (paquete 'chromium' en tu distro), o ejecuta "
            "'playwright install chromium' en una terminal dentro del venv "
            "del proyecto."
        ),
        "errores.pdf_no_abre": "No se pudo abrir el PDF del VMC: {ruta}",
        "errores.semana_no_encontrada": "No se encuentra la semana {fecha} en el VMC.",
        "errores.padlet_sin_clave_publica": "No se ha podido determinar la clave pública del tablón (public_key)",
        "errores.padlet_sin_acceso": "No se ha podido acceder a Padlet ({url}): {error}",
        "errores.padlet_falta_password": "Este tablón está protegido con contraseña y no se ha proporcionado ninguna",
        "errores.padlet_sin_url_password": "El tablón pide contraseña pero no se ha encontrado la URL para enviarla",
        "errores.padlet_sin_csrf": "No se ha encontrado el token CSRF en la página del tablón",
        "errores.padlet_envio_password_fallo": "No se ha podido enviar la contraseña a Padlet: {error}",
        "errores.padlet_password_rechazada": "Contraseña rechazada por Padlet: {detalle}",
        "errores.padlet_password_error_http": "Padlet devolvió un error al enviar la contraseña (HTTP {codigo})",
        "errores.padlet_export_vacio": "El export del tablón no tiene ninguna publicación reconocible — ¿tablón vacío?",
        "errores.padlet_titulo_no_encontrado": "No hay ninguna publicación cuyo título contenga {titulo!r}. Títulos disponibles: {titulos}",
        "errores.padlet_sin_adjunto": "La publicación {titulo!r} no tiene ningún adjunto",
        "errores.padlet_descarga_fallo": "No se ha podido descargar el adjunto de {titulo!r}: {error}",
        "errores.drive_link_invalido": "El enlace de Google Drive no parece válido.",
        "errores.drive_sin_acceso": "No se ha podido acceder a Google Drive: {error}",
        "errores.drive_no_publico": (
            "No se ha podido descargar el archivo — comprueba que está "
            "compartido como \"Cualquiera con el enlace\"."
        ),
        "errores.no_se_pudo_guardar_pdf": "No se ha podido guardar el PDF descargado:\n{error}",
        "errores.no_se_pudo_leer_vmc_padlet": "No se ha podido leer el VMC descargado del Padlet:\n{error}",
        "errores.no_se_pudo_leer_vmc": "No se ha podido leer el VMC:\n{error}",
        "errores.padlet_sin_semanas_asignaciones": (
            "No se ha encontrado ninguna semana con asignaciones en el/los VMC "
            "descargado(s) del Padlet."
        ),
        "errores.padlet_sin_semanas_participantes": (
            "No se ha encontrado ninguna semana con participantes en el/los VMC "
            "descargado(s) del Padlet."
        ),
        "errores.pdf_sin_semanas_asignaciones": (
            "No se ha encontrado ninguna semana con asignaciones en este PDF. "
            "Comprueba que es el archivo VMC correcto."
        ),
        "errores.pdf_sin_semanas_participantes": (
            "No se ha encontrado ninguna semana con participantes en este PDF. "
            "Comprueba que es el archivo VMC correcto."
        ),
        "errores.no_se_pudieron_generar_documentos": "No se han podido generar los documentos:\n{error}",
        "errores.error_enviando_mensajes": "Ha ocurrido un error enviando los mensajes:\n{error}",
        "errores.no_se_pudo_generar_imagen": "No se ha podido generar la imagen de la semana:\n{error}",
        "errores.error_enviando_recordatorios": "Ha ocurrido un error enviando los recordatorios:\n{error}",
        "errores.semana_sin_participantes": "No se ha encontrado ningún participante para esta semana.",
        "errores.semana_pocos_participantes": (
            "Se han detectado {n} participantes, bastante menos que la media de las "
            "demás semanas de este VMC ({media}). Puede que falte algo por un formato "
            "distinto en esta semana — revisa el VMC antes de enviar."
        ),
        "errores.rol_no_detectado": "No se ha detectado \"{rol}\" esta semana.",

        # --- Calendar event text (gcal_link.py, gen_ics.py) — what the
        # recipient sees on their own calendar, not editable from the app
        # like message.txt is (see i18n.py's own docstring above). ---
        "calendario.titulo_evento": "Intervención N. {numero}. {tipo} para {nombre}",
        # Exact wording/spacing kept from the original xlsm macro
        # (ExportarICSdesdeTabla1) on purpose — some calendar clients may
        # already have events from before this rewrite matching this
        # format; changing it isn't just a translation.
        "calendario.titulo_evento_ics": "Intervencion N{numero}. {tipo} para {nombre}",
        "calendario.aviso_1_semana": "Recordatorio - 1 semana antes",
        "calendario.aviso_1_dia": "Recordatorio - 1 día antes",

        # --- cli.py (terminal mode) — app-generated text, not
        # congregation content, so it follows the UI language like
        # errores.* does (see this module's docstring). The flag NAMES
        # themselves (--vmc, --plantilla...) stay fixed regardless of
        # language — only an English alias is added for each in cli.py,
        # never renamed — since a script/alias/README a congregation
        # already wrote using them should keep working. ---
        "cli.ayuda_plantilla": "PLANTILLA ASIGNACIONES.pdf (con el AcroForm)",
        "cli.ayuda_contactos": "CSV con columnas name,phone (ver contacts.example.csv)",
        "cli.ayuda_mensaje": "Plantilla de texto del mensaje de WhatsApp",
        "cli.ayuda_mes": "YYYY-MM: procesar solo ese mes",
        "cli.ayuda_semanas": "Fechas YYYY-MM-DD separadas por coma",
        "cli.ayuda_enviar": "Tras confirmar, enviar por WhatsApp Web (requiere sesión iniciada)",
        "cli.ayuda_recordatorio": "Qué mandar como recordatorio de calendario. Si se omite, se pregunta.",
        "cli.parseando": "Parseando {nombre}...",
        "cli.sin_semanas": "No se encontraron semanas con asignaciones para ese filtro.",
        "cli.cargando_contactos": "Cargando contactos...",
        "cli.generando": "Generando PDF/JPG/ICS...",
        "cli.sin_telefono": "SIN TELÉFONO — revisar a mano",
        "cli.total_generado": "Total: {total} papeletas generadas, {sin_telefono} sin teléfono resuelto.",
        "cli.documentos_en": "Documentos en: {ruta}",
        "cli.excluidos_sin_telefono": "{n} persona(s) sin teléfono resuelto se excluirán del envío.",
        "cli.confirmar_envio": "¿Confirmar envío por WhatsApp? [s/N] ",
        "cli.confirmar_respuesta": "s",
        "cli.cancelado": "Cancelado. No se ha enviado nada.",
        "cli.pregunta_recordatorio": "¿Qué quieres enviar como recordatorio de calendario?",
        "cli.opcion_ics": "1) Archivo .ics (se añade solo al abrir el archivo)",
        "cli.opcion_gcal": "2) Link de Google Calendar (un toque y ya está)",
        "cli.opcion_ambos": "3) Ambos",
        "cli.elige_opcion": "Elige 1/2/3 [3]: ",
        "cli.opcion_invalida": "Opción no válida.",

        # --- migrate_contacts.py (one-off legacy xlsm -> csv migration) ---
        "migrar.uso": "Uso: python -m assistant.migrate_contacts <xlsm> [destino.csv]",
        "migrar.completado": "{total} contactos migrados a {ruta}",

        # --- edit_contacts.py (terminal contact editor) ---
        "editar_contactos.menu": (
            "\n--- Contactos ---\n"
            "1) Listar\n"
            "2) Buscar\n"
            "3) Añadir / actualizar\n"
            "4) Borrar\n"
            "5) Guardar y salir\n"
            "0) Salir sin guardar\n"
        ),
        "editar_contactos.sin_contactos": "(sin contactos)",
        "editar_contactos.buscar_prompt": "Nombre a buscar: ",
        "editar_contactos.nombre_prompt": "Nombre completo: ",
        "editar_contactos.nombre_vacio": "Nombre vacío, cancelado.",
        "editar_contactos.telefono_prompt": "Teléfono (código de país + número, sin '+' ni espacios): ",
        "editar_contactos.telefono_invalido": "El teléfono debe ser solo números (sin '+' ni espacios). Cancelado.",
        "editar_contactos.actualizado": "'{nombre}' ya existía con {anterior} -> actualizado a {nuevo}",
        "editar_contactos.anadido": "Añadido: {nombre} -> {telefono}",
        "editar_contactos.borrar_prompt": "Nombre exacto a borrar: ",
        "editar_contactos.borrado": "Borrado: {nombre}",
        "editar_contactos.no_encontrado": "No se ha encontrado ese nombre exacto. Usa la opción 2 (Buscar) para verlo escrito tal cual.",
        "editar_contactos.cargados": "Cargados {n} contactos de {ruta}",
        "editar_contactos.elige_opcion": "Elige una opción: ",
        "editar_contactos.guardado": "Guardado en {ruta}",
        "editar_contactos.salido_sin_guardar": "Salido sin guardar.",
        "editar_contactos.opcion_invalida": "Opción no válida.",

        # --- whatsapp_send.py / send_reminders.py — terminal progress
        # output while a real send is running (assignments or reminders).
        # Only reaches someone when running from the CLI, not the GUI
        # (which uses on_progreso/on_resultado instead), but it's the
        # same app-generated text as cli.py's, so it follows the UI
        # language the same way. ---
        "envio.escanea_qr": "Escanea el código QR con WhatsApp en tu móvil (Ajustes > Dispositivos vinculados)...",
        "envio.cancelado_usuario": "Cancelado por el usuario.",
        "envio.enviando_a": "Enviando a {nombre} ({telefono})...",
        "envio.navegador_reabriendo": "  El navegador se cerró inesperadamente, reabriendo sesión...",
        "envio.aviso_fallo": "  [AVISO] No se pudo enviar a {nombre}: {error}",
        "envio.ok": "  OK -> {nombre}",
    },
    "en": {
        "app.titulo": "Life & Ministry Assistant",
        "comun.guardar": "Save",
        "comun.cancelar": "Cancel",
        "comun.atras": "Back",
        "comun.siguiente": "Next",
        "comun.elegir": "Choose...",

        "config_inicial.titulo": "Initial setup",
        "config_inicial.mensaje": (
            "Before starting, you need to set the S-89 PDF location "
            "and a few other paths. The settings screen will open now."
        ),

        "home.subtitulo_asignaciones": "ASSIGNMENTS",
        "home.boton_nueva_asignacion": "New weekly assignment",
        "home.boton_historial": "Sending history",
        "home.boton_mensaje": "Assignment message",
        "home.subtitulo_recordatorios": "MEETING REMINDERS",
        "home.boton_nuevo_recordatorio": "Send reminders",
        "home.boton_historial_recordatorios": "Reminder history",
        "home.boton_mensaje_recordatorio": "Reminder message",
        "home.subtitulo_comun": "SHARED",
        "home.boton_contactos": "Contacts",
        "home.boton_config_general": "General settings",
        "home.boton_config_avanzada": "Advanced settings",

        "config_general.titulo_ventana": "General settings",
        "config_general.ayuda": (
            "These paths are set once and used every week. Change them "
            "here whenever you like, without editing any file by hand."
        ),
        "config_general.s89_pdf": "S-89 PDF:",
        "config_general.s89_pdf_dialogo": "Select the S-89 PDF",
        "config_general.carpeta_salida": "Output folder:",
        "config_general.carpeta_salida_dialogo": "Select the output folder",
        "config_general.abrir_carpeta": "Open installation folder",
        "config_general.rutas_titulo": "Paths",
        "config_general.padlet_titulo_corto": "Padlet (optional)",
        "config_general.padlet_url": "Board URL:",
        "config_general.padlet_password": "Password:",
        "config_general.padlet_workbook_title": "Schedule post title:",
        "config_general.drive_titulo_corto": "Google Drive (optional)",
        "config_general.drive_link": "Share link:",
        "config_general.drive_nota": "The file must be shared as \"Anyone with the link\".",
        "config_general.preferencias_titulo": "Language and theme",
        "config_general.idioma": "Language:",
        "config_general.idioma_nota": "The language change applies after restarting the app, same as the theme.",
        "config_general.tema": "Theme:",
        "config_general.tema_claro": "Light",
        "config_general.tema_oscuro": "Dark",
        "config_general.tema_sistema": "Automatic (follow system)",
        "config_general.tema_nota": "The theme change applies after restarting the app.",

        # --- Room labels (models.py) ---
        "room.principal": "Main hall",
        "room.aux1": "Overflow room 1",
        "room.aux2": "Overflow room 2",

        # --- Wizard steps (widgets.py) ---
        "widgets.paso_de": "STEP {actual} OF {total} — {nombre}",
        "pasos.vmc": "Schedule",
        "pasos.semana": "Week",
        "pasos.revisar": "Review",
        "pasos.vista_previa": "Preview",
        "pasos.confirmar": "Confirm",

        # --- Reused across screens ---
        "comun.cerrar": "Close",
        "comun.cerrar_sin_guardar": "Close without saving",
        "comun.probar_conmigo": "Try it with me",
        "comun.tu_telefono": "Your phone:",
        "comun.ejemplo_telefono": "country code + number, no spaces or '+'",
        "comun.enviar_prueba": "Send test",
        "comun.telefono_no_valido_titulo": "Invalid phone number",
        "comun.telefono_no_valido_msg": "The phone number must contain only digits, with country code (no '+' or spaces).",
        "comun.nuevo_contacto_titulo": "New contact",
        "comun.telefono_para": "Phone number for {nombre} (country code + number, no '+' or spaces):",
        "comun.anadir_contacto_tooltip": "Add this person to the contact list with their phone number",
        "comun.usar_sugerencia": "Use {nombre}",
        "comun.usar_sugerencia_tooltip": "Is this the same person as {nombre!r} in the contact list?",
        "comun.abriendo_whatsapp": "Opening WhatsApp Web...",
        "comun.escanea_qr": "Scan the QR code with WhatsApp on your phone (Settings > Linked devices)...",
        "comun.cancelar_envio": "Cancel",
        "comun.reintentar_fallidos": "Retry failed",
        "comun.reintentar_fallidos_n": "Retry failed ({n})",
        "comun.volver_inicio": "Back to home",
        "comun.cancelando": "Cancelling after the current send...",
        "comun.error_enviar_titulo": "Error sending",
        "comun.enviado_n": "Sent {i}/{total}",
        "comun.prueba_enviada": "Test sent. Check your WhatsApp.",
        "comun.prueba_fallo": "Couldn't send: {motivo}",
        "comun.error_desconocido": "unknown error",
        "comun.error_enviar_prueba_titulo": "Error sending the test",
        "comun.guardado_titulo": "Saved",
        "comun.no_se_pudo_enviar": "couldn't be sent",

        # --- VMC picker (assignments and reminders) ---
        "workbook_picker.titulo": "Select the meeting schedule file",
        "workbook_picker.ayuda_asignaciones": (
            "The schedule is the PDF with the Life and Ministry Meeting program, "
            "used to extract names, dates and assignments."
        ),
        "workbook_picker.ayuda_recordatorio": (
            "The schedule is the PDF with the Life and Ministry Meeting program. "
            "Everyone taking part that week will be read from it."
        ),
        "workbook_picker.ningun_archivo": "(no file selected)",
        "workbook_picker.elegir_archivo": "Select schedule file (PDF)",
        "workbook_picker.buscar_padlet": "Search on Padlet",
        "workbook_picker.buscando_padlet": "Searching on Padlet...",
        "workbook_picker.descargado_padlet": "{nombre} (downloaded from Padlet)",
        "workbook_picker.descargado_padlet_generico": "(downloaded from Padlet)",
        "workbook_picker.padlet_falta_titulo": "Padlet isn't set up yet",
        "workbook_picker.padlet_falta_msg": (
            "You haven't set the Padlet board URL yet.\n\n"
            "Go to General settings and fill in the \"Padlet\" section "
            "(URL, password if the board needs one, and the title of the "
            "schedule post)."
        ),
        "workbook_picker.padlet_error_titulo": "Couldn't search on Padlet",
        "workbook_picker.error_leer_titulo": "Couldn't read the schedule file",
        "workbook_picker.dialogo_seleccionar": "Select the schedule file",
        "workbook_picker.fuente_archivo_titulo": "Local file",
        "workbook_picker.fuente_archivo_desc": "Choose a PDF from your computer",
        "workbook_picker.fuente_padlet_titulo": "Padlet",
        "workbook_picker.fuente_padlet_desc_configurado": "Board set up in Settings",
        "workbook_picker.fuente_padlet_desc_sin_configurar": "Not set up — tap to add the board",
        "workbook_picker.fuente_drive_titulo": "Google Drive",
        "workbook_picker.fuente_drive_desc_configurado": "Link set up in Settings",
        "workbook_picker.fuente_drive_desc_sin_configurar": "Not set up — tap to add the link",
        "workbook_picker.listo": "Ready",
        "workbook_picker.buscando_drive": "Downloading from Google Drive...",
        "workbook_picker.descargado_drive": "{nombre} (downloaded from Drive)",
        "workbook_picker.drive_falta_titulo": "Google Drive isn't set up yet",
        "workbook_picker.drive_falta_msg": (
            "You haven't set the Google Drive link yet.\n\n"
            "Go to General settings and paste the share link for the "
            "schedule PDF (with \"Anyone with the link\" access)."
        ),
        "workbook_picker.drive_error_titulo": "Couldn't download from Drive",

        # --- Week picker (assignments) ---
        "week_picker.titulo": "Choose the week (or weeks)",
        "week_picker.ayuda": "Check the weeks you want to generate and send:",
        "week_picker.mes_siguiente": "Select next month",
        "week_picker.mes_siguiente_tag": "next month",
        "week_picker.n_asignaciones": "{n} assignments",
        "week_picker.resumen_semanas": "{n} week(s) selected",
        "week_picker.resumen_asignaciones": "{n} assignment(s) to generate",
        "week_picker.ninguna_titulo": "No week selected",
        "week_picker.ninguna_msg": "Check at least one week to continue.",

        # --- Review assignments ---
        "review.titulo": "Review the assignments",
        "review.ayuda": (
            "You can edit the name, helper or an already-set phone number by double-clicking the cell, "
            "and resize the text columns by dragging their edge. "
            "Uncheck \"Send\" on a row to exclude that person from this batch."
        ),
        "review.col_enviar": "Send",
        "review.col_fecha": "Date",
        "review.col_num": "No.",
        "review.col_tipo": "Part",
        "review.col_sala": "Room",
        "review.col_nombre": "Name",
        "review.col_ayudante": "Helper",
        "review.col_telefono": "Phone",
        "review.col_sugerencia": "Suggestion",  # still used by reminder_review.py's own table
        "review.col_estado": "Status",
        "review.generar_vista_previa": "Generate preview",
        "review.pill_sin_telefono": "No phone",
        "review.pill_enviada_corta": "Sent",
        "review.pill_enviada": "Sent on {fecha}",
        "review.pill_ok": "OK",
        "review.aviso_sin_telefono": "{n} person(s) with no phone number",
        "review.aviso_duplicado": "{n} assignment(s) already sent before (\"Send\" unchecked)",
        "review.revisalas": ". Review them before continuing.",
        "review.tooltip_duplicado": (
            "This assignment was already sent on {fecha} — \"Send\" has been unchecked. "
            "Check it again if you really want to resend it."
        ),

        # --- Preview (assignments) ---
        "preview.titulo": "Preview",
        "preview.generando": "Generating documents...",
        "preview.atras_corregir": "Back, fix something",
        "preview.todo_correcto": "All correct, continue",
        "preview.falta_s89_titulo": "Missing S-89 PDF",
        "preview.falta_s89_msg": (
            "The configured S-89 file can't be found. "
            "Go to General settings and select it."
        ),
        "preview.generando_n": "Generating {i}/{total}: {nombre}...",
        "preview.ayuda": "Review the generated slips before continuing.",
        "preview.n_papeletas_generadas": "{n} slips generated",
        "preview.sin_telefono": "(no phone number)",
        "preview.error_titulo": "Error generating documents",

        # --- Confirm send (assignments) ---
        "send_confirm.titulo": "Confirm sending",
        "send_confirm.pregunta_recordatorio": "What do you want to send as a calendar reminder?",
        "send_confirm.opcion_ics": "ICS file",
        "send_confirm.opcion_gcal": "Google Calendar link",
        "send_confirm.opcion_ambos": "Both",
        "send_confirm.vista_previa_ejemplo": "This is how the message will look (example with the first person):",
        "send_confirm.revisado": "I've reviewed the slips and confirm they're correct.",
        "send_confirm.enviar": "Send",
        "send_confirm.se_van_a_enviar": "{n} messages are going to be sent via WhatsApp.",
        "send_confirm.error_vista_previa": "(Couldn't generate the preview: {error})",

        # --- Sending (assignments) ---
        "sending.titulo": "Sending",
        "sending.terminado_n_fallidos": "Sending finished, {n} failed.",
        "sending.terminado_bien": "Sending finished, all good.",
        "sending.resumen_enviados": "{n} sent",
        "sending.resumen_fallidos": "{n} failed",

        # --- Week picker (meeting reminders) ---
        "rec_semana.titulo": "Choose the week",
        "rec_semana.ayuda": (
            "Choose the week you want to send the reminder for. "
            "Weeks shown in yellow have fewer participants than expected — "
            "it may be worth checking the schedule before sending."
        ),
        "rec_semana.n_participantes": "{n} participants",
        "rec_semana.semana_actual": "This week",
        "rec_semana.semana_siguiente": "Next week",
        "rec_semana.elige_msg": "Choose a week to continue.",
        "rec_semana.incompleta_titulo": "This week looks incomplete",
        "rec_semana.incompleta_continuar": "Do you want to continue anyway?",
        "rec_semana.pill_incompleta": "Incomplete",

        # --- Review recipients (meeting reminders) ---
        "rec_revisar.titulo": "Review the recipients",
        "rec_revisar.ayuda": (
            "You can edit the name or an already-set phone number by double-clicking the cell. "
            "Uncheck \"Send\" on a row to exclude that person from this reminder."
        ),
        "rec_revisar.col_participacion": "Part",
        "rec_revisar.aviso_duplicado": "{n} reminder(s) already sent before (\"Send\" unchecked)",
        "rec_revisar.tooltip_duplicado": (
            "This week's reminder was already sent on {fecha} — "
            "\"Send\" has been unchecked. Check it again if you really want to resend it."
        ),
        "rec_revisar.continuar": "Continue",
        "rec_revisar.nadie_titulo": "Nobody selected",
        "rec_revisar.nadie_msg": "Check \"Send\" on at least one person.",

        # --- Confirm reminder (crop image + message) ---
        "rec_confirmar.titulo": "Preview and confirmation",
        "rec_confirmar.generando_imagen": "Generating the week's image...",
        "rec_confirmar.se_ve_mal": "Does the crop look wrong? Adjust it:",
        "rec_confirmar.borde_superior": "Top edge:",
        "rec_confirmar.borde_inferior": "Bottom edge:",
        "rec_confirmar.mostrar_mas": "Show more",
        "rec_confirmar.mostrar_mas_tooltip": "Expand the crop on this edge",
        "rec_confirmar.recortar_mas": "Crop more",
        "rec_confirmar.recortar_mas_tooltip": "Shrink the crop on this edge",
        "rec_confirmar.restablecer": "Reset crop",
        "rec_confirmar.asi_quedara_para": "This is how the message will look for:",
        "rec_confirmar.revisado": "I've reviewed the image and the message, they're correct.",
        "rec_confirmar.enviar": "Send",
        "rec_confirmar.se_van_a_enviar": "{n} reminders are going to be sent via WhatsApp.",
        "rec_confirmar.error_imagen_titulo": "Error generating the image",

        # --- Sending reminders ---
        "rec_enviando.titulo": "Sending reminders",

        # --- Contacts editor ---
        "contactos.titulo_ventana": "Contacts",
        "contactos.ayuda": (
            "Full name and phone number with country code, no '+' or spaces. "
            "The list sorts itself by name. You can resize the columns."
        ),
        "contactos.buscar_placeholder": "Search by name...",
        "contactos.col_nombre": "Name",
        "contactos.col_telefono": "Phone",
        "contactos.anadir": "+ Add",
        "contactos.borrar_seleccionado": "Delete selected",
        "contactos.telefono_invalido_de": "{nombre}'s phone number must contain only digits (no '+' or spaces).",
        "contactos.n_guardados": "{n} contacts saved.",
        "contactos.n_contactos": "{n} contact(s)",

        # --- History ---
        "historial.titulo_ventana": "Sending history",
        "historial.titulo_recordatorios": "Reminder history",
        "historial.ayuda": "Log of every WhatsApp message sent (or that failed).",
        "historial.col_cuando": "Sent on",
        "historial.col_asignacion": "Assignment",
        "historial.col_nombre": "Name",
        "historial.col_telefono": "Phone",
        "historial.col_estado": "Status",
        "historial.col_motivo": "Reason",
        "historial.vacio": "(nothing sent yet)",
        "historial.pill_fallido": "Failed",
        "historial.n_resultados": "{n} sent",

        # --- Message editor ---
        "mensaje.titulo_ventana": "Edit message",
        "mensaje.titulo_ventana_recordatorio": "Edit reminder message",
        "mensaje.ayuda": "You can use these placeholders in the message, they fill in automatically:\n{name}  {helper}  {date}  {number}  {type}  {link}",
        "mensaje.ayuda_recordatorio": (
            "You can use these placeholders in the message, they fill in automatically:\n"
            "{name}  {first_name}  {role}  {date}  {relative_date}\n"
            "{relative_date} is worked out automatically from when you send the reminder "
            "(\"tomorrow\", \"the day after tomorrow\", \"next week\"...)."
        ),
        "mensaje.guardado_msg": "Message saved.",
        "mensaje.vista_previa": "Preview",
        "mensaje.plantilla_defecto": (
            "Hi {first_name}, just a reminder that you have an assignment coming up "
            "on {date}. You can add it to your calendar using the link or the file "
            "below. Thanks!\n\n{link}"
        ),
        "mensaje.plantilla_defecto_recordatorio": (
            "Good morning {first_name}! Just a reminder that you have a part in the "
            "meeting {relative_date}: {role}. Thank you!"
        ),

        # --- Advanced settings (timing) ---
        "tiempos.titulo_ventana": "Advanced settings — WhatsApp timing",
        "tiempos.ayuda": (
            "Wait times (in seconds) between each step when sending via WhatsApp. "
            "Higher values are slower but safer for the account."
        ),
        "tiempos.espera_abrir_chat": "Wait when opening the chat",
        "tiempos.espera_tras_adjuntar": "Wait after attaching a file",
        "tiempos.espera_tras_cargar": "Wait for the file to finish loading",
        "tiempos.espera_tras_enviar": "Wait after pressing send",
        "tiempos.pausa_entre_contactos": "Pause between each contact",
        "tiempos.restaurar_defecto": "Restore default values",

        # --- Try it with me ---
        "test_send.titulo_ventana": "Try it with me",
        "test_send.ayuda_asignacion": (
            "{nombre}'s slip will be sent to your own number, "
            "so you can check how it looks before the real send."
        ),
        "test_send.ayuda_recordatorio": (
            "{nombre}'s reminder will be sent to your own number, "
            "so you can check how it looks before the real send."
        ),

        # --- Runtime errors (padlet.py, parse_workbook.py,
        # reminder_workbook.py, whatsapp_send.py, gui/workers.py) ---
        "errores.plantilla_no_encontrada": (
            "{ruta} doesn't exist yet. Create it with the message text — open "
            "\"Assignment message\" or \"Reminder message\" from the app to see "
            "the available placeholders and save it."
        ),
        "errores.sin_navegador": (
            "Couldn't open any Chromium/Chrome/Edge browser. Install Google "
            "Chrome, use Microsoft Edge (comes with Windows), install Chromium "
            "(the 'chromium' package on your distro), or run "
            "'playwright install chromium' in a terminal inside the project's "
            "venv."
        ),
        "errores.pdf_no_abre": "Couldn't open the schedule PDF: {ruta}",
        "errores.semana_no_encontrada": "Week {fecha} isn't in the schedule.",
        "errores.padlet_sin_clave_publica": "Couldn't determine the board's public key (public_key)",
        "errores.padlet_sin_acceso": "Couldn't access Padlet ({url}): {error}",
        "errores.padlet_falta_password": "This board is password-protected and no password was provided",
        "errores.padlet_sin_url_password": "The board asks for a password but no URL to submit it was found",
        "errores.padlet_sin_csrf": "Couldn't find the CSRF token on the board's page",
        "errores.padlet_envio_password_fallo": "Couldn't submit the password to Padlet: {error}",
        "errores.padlet_password_rechazada": "Password rejected by Padlet: {detalle}",
        "errores.padlet_password_error_http": "Padlet returned an error submitting the password (HTTP {codigo})",
        "errores.padlet_export_vacio": "The board's export doesn't have any recognizable post — is the board empty?",
        "errores.padlet_titulo_no_encontrado": "There's no post whose title contains {titulo!r}. Available titles: {titulos}",
        "errores.padlet_sin_adjunto": "The post {titulo!r} doesn't have any attachment",
        "errores.padlet_descarga_fallo": "Couldn't download the attachment from {titulo!r}: {error}",
        "errores.drive_link_invalido": "The Google Drive link doesn't look valid.",
        "errores.drive_sin_acceso": "Couldn't access Google Drive: {error}",
        "errores.drive_no_publico": (
            "Couldn't download the file — check that it's shared as "
            "\"Anyone with the link\"."
        ),
        "errores.no_se_pudo_guardar_pdf": "Couldn't save the downloaded PDF:\n{error}",
        "errores.no_se_pudo_leer_vmc_padlet": "Couldn't read the schedule downloaded from Padlet:\n{error}",
        "errores.no_se_pudo_leer_vmc": "Couldn't read the schedule file:\n{error}",
        "errores.padlet_sin_semanas_asignaciones": (
            "No week with assignments was found in the schedule file(s) "
            "downloaded from Padlet."
        ),
        "errores.padlet_sin_semanas_participantes": (
            "No week with participants was found in the schedule file(s) "
            "downloaded from Padlet."
        ),
        "errores.pdf_sin_semanas_asignaciones": (
            "No week with assignments was found in this PDF. Check that it's "
            "the right schedule file."
        ),
        "errores.pdf_sin_semanas_participantes": (
            "No week with participants was found in this PDF. Check that it's "
            "the right schedule file."
        ),
        "errores.no_se_pudieron_generar_documentos": "Couldn't generate the documents:\n{error}",
        "errores.error_enviando_mensajes": "An error occurred while sending the messages:\n{error}",
        "errores.no_se_pudo_generar_imagen": "Couldn't generate the week's image:\n{error}",
        "errores.error_enviando_recordatorios": "An error occurred while sending the reminders:\n{error}",
        "errores.semana_sin_participantes": "No participants were found for this week.",
        "errores.semana_pocos_participantes": (
            "{n} participants were found, quite a bit fewer than the average for the "
            "other weeks in this schedule ({media}). Something may be missing due to a "
            "different format this week — check the schedule before sending."
        ),
        "errores.rol_no_detectado": "\"{rol}\" wasn't found this week.",

        # --- Calendar event text (gcal_link.py, gen_ics.py) — what the
        # recipient sees on their own calendar, not editable from the app
        # like message.txt is (see i18n.py's own docstring above). ---
        "calendario.titulo_evento": "Assignment No. {numero}. {tipo} for {nombre}",
        "calendario.titulo_evento_ics": "Assignment No.{numero}. {tipo} for {nombre}",
        "calendario.aviso_1_semana": "Reminder - 1 week before",
        "calendario.aviso_1_dia": "Reminder - 1 day before",

        # --- cli.py (terminal mode) — see the matching Spanish section
        # above for why this follows the UI language. ---
        "cli.ayuda_plantilla": "The S-89 assignment template PDF (with the AcroForm)",
        "cli.ayuda_contactos": "CSV with name,phone columns (see contacts.example.csv)",
        "cli.ayuda_mensaje": "WhatsApp message text template",
        "cli.ayuda_mes": "YYYY-MM: process only that month",
        "cli.ayuda_semanas": "YYYY-MM-DD dates, comma-separated",
        "cli.ayuda_enviar": "After confirming, send over WhatsApp Web (requires a logged-in session)",
        "cli.ayuda_recordatorio": "What to send as the calendar reminder. If omitted, you'll be asked.",
        "cli.parseando": "Parsing {nombre}...",
        "cli.sin_semanas": "No weeks with assignments were found for that filter.",
        "cli.cargando_contactos": "Loading contacts...",
        "cli.generando": "Generating PDF/JPG/ICS...",
        "cli.sin_telefono": "NO PHONE — needs a manual check",
        "cli.total_generado": "Total: {total} slips generated, {sin_telefono} with no phone resolved.",
        "cli.documentos_en": "Documents in: {ruta}",
        "cli.excluidos_sin_telefono": "{n} people with no phone resolved will be excluded from sending.",
        "cli.confirmar_envio": "Confirm sending over WhatsApp? [y/N] ",
        "cli.confirmar_respuesta": "y",
        "cli.cancelado": "Cancelled. Nothing was sent.",
        "cli.pregunta_recordatorio": "What do you want to send as the calendar reminder?",
        "cli.opcion_ics": "1) .ics file (added automatically when opened)",
        "cli.opcion_gcal": "2) Google Calendar link (one tap and done)",
        "cli.opcion_ambos": "3) Both",
        "cli.elige_opcion": "Choose 1/2/3 [3]: ",
        "cli.opcion_invalida": "Not a valid option.",

        # --- migrate_contacts.py (one-off legacy xlsm -> csv migration) ---
        "migrar.uso": "Usage: python -m assistant.migrate_contacts <xlsm> [destination.csv]",
        "migrar.completado": "{total} contacts migrated to {ruta}",

        # --- edit_contacts.py (terminal contact editor) ---
        "editar_contactos.menu": (
            "\n--- Contacts ---\n"
            "1) List\n"
            "2) Search\n"
            "3) Add / update\n"
            "4) Delete\n"
            "5) Save and exit\n"
            "0) Exit without saving\n"
        ),
        "editar_contactos.sin_contactos": "(no contacts)",
        "editar_contactos.buscar_prompt": "Name to search for: ",
        "editar_contactos.nombre_prompt": "Full name: ",
        "editar_contactos.nombre_vacio": "Empty name, cancelled.",
        "editar_contactos.telefono_prompt": "Phone (country code + number, no '+' or spaces): ",
        "editar_contactos.telefono_invalido": "The phone number must be digits only (no '+' or spaces). Cancelled.",
        "editar_contactos.actualizado": "'{nombre}' already existed with {anterior} -> updated to {nuevo}",
        "editar_contactos.anadido": "Added: {nombre} -> {telefono}",
        "editar_contactos.borrar_prompt": "Exact name to delete: ",
        "editar_contactos.borrado": "Deleted: {nombre}",
        "editar_contactos.no_encontrado": "That exact name wasn't found. Use option 2 (Search) to see it written exactly as stored.",
        "editar_contactos.cargados": "Loaded {n} contacts from {ruta}",
        "editar_contactos.elige_opcion": "Choose an option: ",
        "editar_contactos.guardado": "Saved to {ruta}",
        "editar_contactos.salido_sin_guardar": "Exited without saving.",
        "editar_contactos.opcion_invalida": "Not a valid option.",

        # --- whatsapp_send.py / send_reminders.py — see the matching
        # Spanish section above for why this follows the UI language. ---
        "envio.escanea_qr": "Scan the QR code with WhatsApp on your phone (Settings > Linked Devices)...",
        "envio.cancelado_usuario": "Cancelled by the user.",
        "envio.enviando_a": "Sending to {nombre} ({telefono})...",
        "envio.navegador_reabriendo": "  The browser closed unexpectedly, reopening session...",
        "envio.aviso_fallo": "  [WARNING] Couldn't send to {nombre}: {error}",
        "envio.ok": "  OK -> {nombre}",
    },
}
