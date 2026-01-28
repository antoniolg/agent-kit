---
name: weekly-newsletter
description: "Genera la newsletter semanal de DevExpert recopilando contenido de X, YouTube, Postiz y bookmarks. Crea borrador en Listmonk para revisión."
---

# Weekly Newsletter DevExpert

Genera la newsletter semanal recopilando todo el contenido publicado y programado de la semana.

## Cuándo se usa

- Cada jueves antes de enviar la newsletter
- El rango de contenido es: **viernes anterior hasta jueves actual** (inclusive)

## Flujo de trabajo

### 1. Recopilar contenido de todas las fuentes

**X/Twitter** (bird CLI):
```bash
bird user-tweets antonioleivag -n 50 --json
```
Filtrar por fechas del rango.

**Postiz** (posts programados):
```bash
postiz posts list --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

**YouTube** (vídeos publicados o programados):
```bash
python list_videos.py --limit 10
```
Usa el script `list_videos.py` incluido en la skill `youtube-publish` (carpeta `scripts/`).

**Bookmarks de X** (lecturas recomendadas):
```bash
bird bookmarks -n 50
```
Filtrar por fechas del rango.

### 2. Proponer lista de temas al usuario

Presentar todos los temas encontrados en categorías:

- **Vídeos propios** (YouTube)
- **Reflexiones/Opinión** (posts largos)
- **Técnico** (hilos, artículos)
- **Personal** (logros, anuncios)
- **De terceros** (bookmarks interesantes)

El usuario selecciona cuáles entran en la newsletter.

### 3. Crear borrador en Listmonk

```bash
listmonk campaigns create \
  --name "Newsletter semanal - DD mes YYYY" \
  --subject "<subject atractivo>" \
  --lists 3 \
  --template-id 1 \
  --content-type markdown \
  --body-file <path-to-content.md>
```

Para actualizar:
```bash
listmonk campaigns update <id> \
  --subject "..." \
  --body-file <path> \
  --lists 3
```

## Estructura de la newsletter

```markdown
¡Hola!

[Intro 2-3 líneas contextualizando la semana]

---

## El vídeo de la semana: [Título]

[Descripción breve del vídeo principal]

[Ver el vídeo en YouTube](URL)

---

## Lo que ha pasado esta semana

**[Tema 1]**

[Descripción + opinión]

[Enlace]

**[Tema 2]**

[...]

---

## Lectura recomendada: [Título de tercero]

[Por qué es interesante, puntos clave]

[Enlace]

---

## Reflexión de la semana: [Título]

[Reflexión personal más extensa]

[Enlace]

---

## Próxima edición de AI Expert

[CTA fijo hacia devexpert.io]

[Toda la información aquí](https://devexpert.io/cursos/expert/ai)

---

Un abrazo,

Antonio.
```

## Reglas de estilo

- **Tono**: Directo, sin rodeos, con criterio técnico
- **Emojis**: Mínimos (0-2 en todo el email)
- **Enlaces**: Alternar entre X y LinkedIn para distribuir tráfico
- **No incluir**: El vídeo de la semana anterior si ya salió en la newsletter previa
- **Bookmarks**: Usar para "Lectura recomendada" - contenido de terceros que aporta valor

## Parámetros de Listmonk

- **Lista**: DevExpert (id: 3)
- **Template**: DevExpert (id: 1)
- **Content-type**: markdown

## Notas

- La newsletter se queda en estado `draft` hasta que Antonio la revise y programe
- Los enlaces a vídeos privados de YouTube funcionan una vez se publican
- Si hay vídeo programado para el jueves, incluir el enlace aunque esté privado
