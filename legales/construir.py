#!/usr/bin/env python3
"""
Arma las páginas legales de AIMA a partir de la fuente, que vive en el repo del CRM.

    python3 legales/construir.py                 # borrador: con cartel y noindex
    python3 legales/construir.py --verificar     # ¿las páginas están al día con la fuente?
    python3 legales/construir.py --publicar --fecha 2026-10-05   # la fecha de HOY

Cada publicación deja la versión vigente en /aima/agente/terminos/ y una copia
que no cambia nunca más en /aima/agente/terminos/2026-10-05/ — ver
publicar_documento().

LA FUENTE NO ESTÁ ACÁ. Está en ~/productos_digitales/CRM/legales/, y se lee siempre
de origin/main —nunca del disco—: lo que manda es lo mergeado, no lo que alguien
tenga a medio editar. Las copias de ~/Documents/Level Up/ están viejas y no se usan.

Las páginas generadas NO se editan a mano: se corrige la fuente y se vuelve a correr
esto. Cada página lleva anotado de qué commit y de qué texto salió.

QUÉ SE PUBLICA DE CADA ARCHIVO. Los dos tienen notas internas arriba y material de
trabajo abajo. Se toma desde el título que precede a "Última actualización" hasta el
final de la sección "N. Contacto", y nada más. Se corta por los títulos, no por
números de línea, porque el texto va a cambiar. Afuera quedan, por decisión de
legales (21/9): las notas internas, el Anexo I, las Condiciones particulares, el
registro de cambios y la verificación técnica.

EL SCRIPT SE NIEGA A ESCRIBIR si encuentra algo que no puede salir:
  · restos de material interno (títulos de anexos, notas, marcas de borrador)
  · cualquier importe en moneda — el precio de AIMA no se publica (Nico, 21/9)
  · "[FECHA]" sin completar, al publicar
Las palabras de marca ("CRM", "agencia") solo se avisan: si el texto legal las
usa, no se cambian acá — se le avisa a legales.
"""

import argparse
import hashlib
import html
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Falta el módulo markdown:  python3 -m pip install markdown")

RAIZ = Path(__file__).resolve().parent.parent
CRM = Path.home() / "productos_digitales" / "CRM"
REFERENCIA = "origin/main"
PLANTILLA = RAIZ / "legales" / "plantilla.html"

# LO QUE SALE A INTERNET. Todo lo que está en una página publicada se lee en su
# código fuente, comentarios incluidos. Por eso el comentario de cada página
# lleva solo lo que el script necesita para rearmarla —commit, huella del texto,
# fechas— y nada de rutas locales, nombres de repos ni de herramientas
# ("cumplir no es exponer", legales 21/9). Por la misma razón las explicaciones
# viven acá y no en la plantilla: por ejemplo, que estas páginas usan la
# tipografía del sistema y no piden nada a terceros porque el sitio principal
# carga Archivo desde Google Fonts, que le manda la IP de cada visitante a
# Google. Y esta carpeta entera está en .vercelignore: el sitio sirve cualquier
# archivo del repo, y este script tiene rutas y notas internas.

# Las versiones archivadas no se indexan: siguen públicas en su dirección —para
# que un documento firmado se pueda verificar—, pero el buscador muestra solo la
# vigente. La vigente sí se indexa: una política de privacidad tiene que poder
# encontrarse.
ROBOTS_ARCHIVO = '<meta name="robots" content="noindex">'

DOCUMENTOS = {
    "terminos": {
        "fuente": "legales/terminos-agente-aima.md",
        "destino": "aima/agente/terminos/index.html",
        "titulo": "Términos del servicio del agente",
    },
    "privacidad": {
        "fuente": "legales/privacidad-agente-aima.md",
        "destino": "aima/privacidad/index.html",
        "titulo": "Política de privacidad de AIMA",
    },
}

# Títulos que marcan material interno. Se buscan como TÍTULO, no como palabra:
# el texto público menciona el "Anexo I" y las "Condiciones particulares", y está
# bien que lo haga — lo que no puede aparecer es la sección entera.
TITULOS_INTERNOS = re.compile(
    r"^#{1,6}\s*(ANEXO|CONDICIONES PARTICULARES|Notas internas|Registro de cambios|"
    r"Verificación técnica|La estructura|ALCANCE)",
    re.IGNORECASE | re.MULTILINE,
)
# El 21/9 esta lista frenó una nota de verificación ("✅ Verificada contra el
# código el 13/9 por el chat del CRM…") metida ADENTRO de la sección 6 de la
# privacidad, entre el título y el cuerpo: cortar por títulos no alcanza, las
# notas también aparecen en el medio. Los emojis de estado no van en un texto
# legal, así que se tratan como marca de nota.
MARCAS_INTERNAS = ["BORRADOR", "No se publica", "⏳", "HANDOFF", "[ABOGADO]",
                   "chat de legales", "chat del CRM", "Nota interna",
                   "✅", "⚠️", "🔒", "📌"]
# Cualquier importe en moneda. "dólares" como palabra sí puede estar (la cláusula
# de moneda la necesita); un número al lado de un signo de moneda, no.
PRECIO = re.compile(r"(USD|U\$S|US\$|\$\s?\d)")
# "Agencia de Acceso a la Información Pública" es el órgano de control de la Ley
# 25.326: la política está obligada a nombrarlo. La regla de marca es no llamar
# "agencia" a Level Up, no borrar el nombre de un organismo.
MARCA = [(re.compile(r"\bCRM\b"), "CRM"),
         (re.compile(r"\bagencias?\b(?! de Acceso a la Información Pública)", re.IGNORECASE), "agencia")]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


class Rechazo(Exception):
    """Algo en el texto impide escribir la página."""


def git(*args):
    return subprocess.run(["git", "-C", str(CRM), *args], check=True,
                          capture_output=True, text=True).stdout


def leer_fuente(ruta):
    texto = git("show", f"{REFERENCIA}:{ruta}")
    commit = git("log", "-1", "--format=%h", REFERENCIA, "--", ruta).strip()
    return texto, commit


def extraer(texto, nombre):
    lineas = texto.splitlines()
    try:
        fecha = next(i for i, l in enumerate(lineas) if l.startswith("**Última actualización:**"))
    except StopIteration:
        raise Rechazo(f"{nombre}: no encuentro la línea «**Última actualización:**»")
    inicio = next((i for i in range(fecha, -1, -1) if lineas[i].startswith("# ")), None)
    if inicio is None:
        raise Rechazo(f"{nombre}: no hay un título antes de «Última actualización»")

    contacto = [i for i in range(inicio, len(lineas))
                if re.match(r"^## \d+\. Contacto\s*$", lineas[i])]
    if len(contacto) != 1:
        raise Rechazo(f"{nombre}: esperaba UNA sección «N. Contacto» y encontré {len(contacto)}")
    fin = next((i for i in range(contacto[0] + 1, len(lineas))
                if re.match(r"^---\s*$", lineas[i]) or re.match(r"^#{1,6} ", lineas[i])),
               len(lineas))
    return "\n".join(lineas[inicio:fin]).strip() + "\n"


def revisar(publico, nombre, publicar):
    problemas = []
    for m in TITULOS_INTERNOS.finditer(publico):
        problemas.append(f"título interno: «{m.group(0).strip()}»")
    for marca in MARCAS_INTERNAS:
        if marca in publico:
            problemas.append(f"marca interna: «{marca}»")
    for n, linea in enumerate(publico.splitlines(), 1):
        if PRECIO.search(linea):
            problemas.append(f"importe en moneda (línea {n}): {linea.strip()[:90]}")
    if publicar and "[FECHA]" in publico:
        problemas.append("«[FECHA]» sin completar — usá --fecha AAAA-MM-DD")
    if problemas:
        raise Rechazo(f"{nombre}: no se escribe nada.\n  · " + "\n  · ".join(problemas))

    avisos = []
    for n, linea in enumerate(publico.splitlines(), 1):
        for patron, palabra in MARCA:
            if patron.search(linea):
                avisos.append(f"«{palabra}» (línea {n}): {linea.strip()[:90]}")
    return avisos


def fecha_larga(iso):
    anio, mes, dia = (int(x) for x in iso.split("-"))
    return f"{dia} de {MESES[mes - 1]} de {anio}"


def ancla(valor, separador):
    # anclas en ASCII: una cláusula se cita como #6-precio-y-forma-de-pago, no
    # con los acentos codificados en la dirección
    valor = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", separador, valor.lower()).strip(separador)


def apilable(m):
    """
    Cada celda lleva el título de su columna en data-label, para que en el
    celular la tabla se lea apilada, una ficha por fila. Deslizando de costado
    no alcanzaba: en la tabla de proveedores de la privacidad, la columna
    "Dónde" —a qué país viajan los datos, lo legalmente importante— quedaba
    cortada en "Determinac…", sin ninguna señal de que seguía.
    """
    tabla = m.group(0)
    titulos = [html.escape(re.sub(r"<[^>]+>", "", t).strip(), quote=True)
               for t in re.findall(r"<th[^>]*>(.*?)</th>", tabla, flags=re.DOTALL)]

    def fila(mf):
        celdas = iter(titulos)
        return re.sub(r"<td([^>]*)>",
                      lambda mc: f'<td{mc.group(1)} data-label="{next(celdas, "")}">', mf.group(0))

    tabla = re.sub(r"<tr>.*?</tr>", fila, tabla, flags=re.DOTALL)
    return f'<div class="tabla">{tabla}</div>'


def base_url(nombre):
    return "/" + DOCUMENTOS[nombre]["destino"].removesuffix("index.html")


def fecha_corta(iso):
    anio, mes, dia = (int(x) for x in iso.split("-"))
    return f"{dia}/{mes}/{anio}"


HOY = date.today().isoformat()   # se puede fijar con --hoy, solo para probar


def meta(pagina_html):
    """Fecha de publicación y rige-desde anotadas en el comentario de una página."""
    f = re.search(r"· fecha (\d{4}-\d{2}-\d{2})", pagina_html)
    r = re.search(r"· rige (\d{4}-\d{2}-\d{2})", pagina_html)
    fecha = f.group(1) if f else None
    return fecha, (r.group(1) if r else fecha)


def versiones_publicadas(nombre):
    """Las versiones archivadas, de la más nueva a la más vieja: [(fecha, rige), …]."""
    carpeta = (RAIZ / DOCUMENTOS[nombre]["destino"]).parent
    if not carpeta.exists():
        return []
    fechas = sorted((d.name for d in carpeta.iterdir()
                     if re.match(r"^\d{4}-\d{2}-\d{2}$", d.name) and (d / "index.html").exists()),
                    reverse=True)
    return [(f, meta((carpeta / f / "index.html").read_text())[1] or f) for f in fechas]


def linea_vigente(nombre, fecha, rige):
    """
    La línea que dice qué versión rige HOY. Redacción de legales (21/9), textual.

    Mientras hay un aviso abierto (la rige-desde de esta versión todavía no
    llegó), para los Negocios ya contratados sigue rigiendo "la versión que les
    regía": la última publicada cuya rige-desde ya pasó. No "la anterior a
    esta" — con dos avisos seguidos esa sería una que nunca rigió.

    Cuando el aviso vence, la línea correcta pasa a ser la de una sola fecha.
    La página vigente es estática, así que eso requiere volver a armarla:
    --verificar lo detecta y --refrescar lo hace.
    """
    url = base_url(nombre)
    otras = [(f, r) for f, r in versiones_publicadas(nombre) if f != fecha]
    permanente = f'<a href="{url}{fecha}/">Dirección permanente de esta versión</a>'

    if rige <= HOY:
        texto = f"Versión vigente, publicada el {fecha_larga(fecha)}. {permanente}"
    else:
        regia = next(((f, r) for f, r in otras if r <= HOY), None)
        if regia is None:
            raise Rechazo(f"{nombre}: aviso abierto hasta el {rige}, pero no hay ninguna versión "
                          "que ya esté rigiendo para nombrar")
        texto = (f"Versión publicada el {fecha_larga(fecha)}. Para los Negocios que ya contrataron, "
                 f"rige desde el {fecha_larga(rige)}; hasta entonces sigue rigiendo la "
                 f'<a href="{url}{regia[0]}/">versión del {fecha_larga(regia[0])}</a>. '
                 f"Los Negocios que contraten desde hoy quedan sujetos a esta. {permanente}")
    if otras:
        texto += " · Versiones anteriores: " + ", ".join(
            f'<a href="{url}{f}/">{fecha_corta(f)}</a>' for f, _ in otras)
    return f'<p class="version">{texto}</p>'


def linea_archivo(nombre, fecha, rige):
    # Una versión archivada no cambia nunca más, así que no puede decir "hasta
    # el X" (legales). Dice cuándo se publicó y, si difiere, desde cuándo rige
    # para los ya contratados — para los nuevos rige desde la firma.
    texto = f"Versión publicada el {fecha_larga(fecha)}"
    if rige != fecha:
        texto += f"; para los Negocios que ya contrataron, rige desde el {fecha_larga(rige)}"
    return (f'<p class="version">{texto}. '
            f'<a href="{base_url(nombre)}">Ver la versión vigente</a></p>')


def armar(nombre, publicar, fecha, version="", estado=None, rige=None):
    doc = DOCUMENTOS[nombre]
    texto, commit = leer_fuente(doc["fuente"])
    publico = extraer(texto, nombre)
    # La fecha de publicación se pone en UN solo lugar: acá, con --fecha. Si la
    # fuente ya trajera una, la dirección de la versión y la fecha impresa
    # podrían no coincidir — que es justo lo que las Condiciones particulares
    # no pueden tolerar, porque citan "la versión del dd/mm/aaaa".
    if publicar and "[FECHA]" not in publico:
        raise Rechazo(f"{nombre}: la fuente ya no dice «[FECHA]». La fecha de publicación la "
                      "pone este script, una sola vez — la fuente tiene que dejar el hueco.")
    if fecha:
        publico = publico.replace("[FECHA]", fecha_larga(fecha))
    avisos = revisar(publico, nombre, publicar)

    cuerpo = markdown.markdown(
        publico, output_format="html",
        extensions=["tables", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": ancla}},
    )
    cuerpo = re.sub(r"<table>.*?</table>", apilable, cuerpo, flags=re.DOTALL)

    huella = hashlib.sha256(publico.encode()).hexdigest()[:16]
    estado = estado or ("publicado" if publicar else "borrador")
    procedencia = (
        "<!--\n"
        f"  commit: {commit}\n"
        f"  texto:  sha256 {huella}\n"
        f"  estado: {estado}" + (f" · fecha {fecha}" if fecha else "")
        + (f" · rige {rige}" if rige else "") + "\n"
        "-->"
    )
    pagina = (PLANTILLA.read_text()
              .replace("{{titulo}}", doc["titulo"])
              .replace("{{procedencia}}", procedencia)
              .replace("{{robots}}", ROBOTS_ARCHIVO if estado == "archivo" else
                       "" if publicar else '<meta name="robots" content="noindex,nofollow">')
              .replace("{{aviso_borrador}}", "" if publicar else
                       '<div class="borrador">BORRADOR — no publicado. '
                       'Pendiente de revisión del abogado.</div>')
              .replace("{{version}}", version)
              .replace("{{contenido}}", cuerpo))
    return doc["destino"], pagina, commit, avisos


def sin_commit(html):
    return re.sub(r"^  commit: .*$", "", html, flags=re.MULTILINE)


def publicar_documento(nombre, fecha, rige, con_aviso_abierto=False):
    """
    UNA DIRECCIÓN POR VERSIÓN (pedido de legales, 21/9). Las Condiciones
    particulares atan cada firma a "la versión del dd/mm/aaaa" de los términos.
    Si la página cambia después, el documento firmado apuntaría a un texto que
    ya no está en línea. Por eso cada publicación escribe dos archivos:

      /aima/agente/terminos/              la vigente, que cambia con cada versión
      /aima/agente/terminos/2026-10-05/   esa versión, que NO cambia nunca más

    Una versión ya publicada no se pisa: si la carpeta con esa fecha existe y el
    contenido difiere, el script se niega. Publicar un cambio es publicar con
    otra fecha.

    AVISOS ABIERTOS (cláusula 14 y reglas de legales, 21/9). Un cambio
    sustancial rige para los ya contratados a los 30 días de notificado; eso se
    publica con --rige-desde. Cada versión es el texto COMPLETO, no un parche:
    una versión nueva arrastra lo que tenga en aviso la anterior. De ahí:
      1. con un aviso abierto no se publica otra versión, salvo con
         --con-aviso-abierto;
      2. y aun así, la nueva no puede regir antes que la que sigue en aviso —
         si no, le aplicaría el cambio en aviso a los ya contratados antes de
         tiempo, que es incumplir la 14.
    La regla de los 30 días NO está acá: el script no sabe qué cambio es
    sustancial. rige-desde es libre, pero nunca anterior a la publicación.
    """
    destino = RAIZ / DOCUMENTOS[nombre]["destino"]
    archivo = destino.parent / fecha / "index.html"
    otras = [(f, r) for f, r in versiones_publicadas(nombre) if f != fecha]

    if rige < fecha:
        raise Rechazo(f"{nombre}: --rige-desde {rige} es anterior a la publicación ({fecha})")
    if otras and fecha < otras[0][0]:
        raise Rechazo(f"{nombre}: ya hay una versión más nueva ({otras[0][0]}); "
                      f"no se publica una del {fecha} por encima")
    if not otras and rige != fecha:
        raise Rechazo(f"{nombre}: es la primera versión — no hay Negocios contratados a quienes "
                      "darles aviso. Rige desde la publicación: sacá --rige-desde.")
    abiertos = [(f, r) for f, r in otras if r > HOY]
    if abiertos and not con_aviso_abierto:
        f, r = abiertos[0]
        raise Rechazo(f"{nombre}: la versión del {f} está en aviso hasta el {r}. Mientras tanto no "
                      "se publica otra: la nueva arrastraría ese cambio. Si hace falta igual, "
                      "--con-aviso-abierto.")
    tope = max((r for _, r in otras), default=fecha)
    if rige < tope:
        raise Rechazo(f"{nombre}: --rige-desde {rige} es anterior al {tope}, cuando empieza a regir "
                      "la versión en aviso. La nueva la contiene, así que no puede regir antes.")

    _, pagina_archivo, commit, avisos = armar(nombre, True, fecha, linea_archivo(nombre, fecha, rige),
                                              estado="archivo", rige=rige)
    if archivo.exists() and archivo.read_text() != pagina_archivo:
        raise Rechazo(f"{nombre}: la versión del {fecha} ya está publicada y su texto es otro. "
                      "Una versión publicada no se pisa: publicá el cambio con otra fecha.")
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(pagina_archivo)
    destino.write_text(vigente_desde_archivo(nombre))
    return commit, avisos, archivo


def vigente_desde_archivo(nombre):
    """
    La página vigente se deriva SIEMPRE de la última versión archivada, nunca de
    la fuente. Si se rearmara desde la fuente —por ejemplo, para actualizar la
    línea cuando vence un aviso— y legales hubiera cambiado el texto mientras
    tanto, la vigente mostraría texto nuevo sin versión con fecha: exactamente
    lo que las direcciones por versión existen para impedir. Así, el texto de la
    vigente es por construcción el de una versión publicada; solo cambia la línea.
    """
    fecha, rige = versiones_publicadas(nombre)[0]
    archivo = (RAIZ / DOCUMENTOS[nombre]["destino"]).parent / fecha / "index.html"
    html = archivo.read_text()
    html, n = re.subn(r'<p class="version">.*?</p>', lambda _: linea_vigente(nombre, fecha, rige),
                      html, count=1, flags=re.DOTALL)
    if n != 1:
        raise Rechazo(f"{nombre}: la versión del {fecha} no tiene la línea de versión")
    return (html.replace("  estado: archivo", "  estado: publicado", 1)
                .replace(ROBOTS_ARCHIVO, "", 1))


def main():
    p = argparse.ArgumentParser(description="Páginas legales de AIMA desde la fuente del CRM.")
    p.add_argument("--publicar", action="store_true",
                   help="sin cartel ni noindex; escribe la vigente y la versión con fecha")
    p.add_argument("--fecha", help="AAAA-MM-DD, la fecha REAL de publicación")
    p.add_argument("--otra-fecha", action="store_true",
                   help="permite una --fecha distinta de hoy (solo si sabés por qué)")
    p.add_argument("--verificar", action="store_true", help="compara lo escrito con la fuente, sin escribir")
    p.add_argument("--rige-desde", help="AAAA-MM-DD: desde cuándo rige para los ya contratados "
                   "(por defecto, la fecha de publicación)")
    p.add_argument("--con-aviso-abierto", action="store_true",
                   help="permite publicar mientras otra versión está en aviso")
    p.add_argument("--refrescar", action="store_true",
                   help="rearma la vigente desde su versión archivada (p. ej. cuando vence un aviso)")
    p.add_argument("--solo", choices=DOCUMENTOS, help="un solo documento")
    p.add_argument("--sin-fetch", action="store_true", help="no traer origin/main antes de leer")
    p.add_argument("--hoy", help=argparse.SUPPRESS)   # solo para probar: fija el día de hoy
    a = p.parse_args()

    global HOY
    if a.hoy:
        HOY = a.hoy
    for opcion in (a.fecha, a.rige_desde, a.hoy):
        if opcion and not re.match(r"^\d{4}-\d{2}-\d{2}$", opcion):
            sys.exit("las fechas van como AAAA-MM-DD")
    if a.publicar:
        if not a.fecha:
            sys.exit("--publicar necesita --fecha AAAA-MM-DD")
        # "Última actualización" tiene que ser la fecha real de publicación, no la
        # del armado (legales, 21/9). Se publica el mismo día que se arma.
        if a.fecha != HOY and not a.otra_fecha:
            sys.exit(f"--fecha {a.fecha} no es hoy ({HOY}). La fecha tiene que ser la del día en que "
                     "esto llega a producción: armá y publicá el mismo día. "
                     "Si hay una razón para otra fecha, agregá --otra-fecha.")
    if not a.sin_fetch:
        try:
            git("fetch", "-q", "origin", "main")
        except subprocess.CalledProcessError:
            print("⚠ no pude traer origin/main — uso lo que hay localmente", file=sys.stderr)

    fallo = False
    for nombre in ([a.solo] if a.solo else DOCUMENTOS):
        destino = RAIZ / DOCUMENTOS[nombre]["destino"]
        try:
            if a.publicar:
                rige = a.rige_desde or a.fecha
                commit, avisos, archivo = publicar_documento(nombre, a.fecha, rige, a.con_aviso_abierto)
                for aviso in avisos:
                    print(f"  ⚠ {nombre} — marca, avisar a legales: {aviso}", file=sys.stderr)
                extra = f", rige desde {rige} para los ya contratados" if rige != a.fecha else ""
                print(f"✓ {nombre}: {DOCUMENTOS[nombre]['destino']} y "
                      f"{archivo.relative_to(RAIZ)}  (publicable, fuente {commit}{extra})")
                continue

            publicadas = versiones_publicadas(nombre)

            if a.refrescar:
                if not publicadas:
                    print(f"✗ {nombre}: no hay ninguna versión publicada que refrescar")
                    fallo = True
                    continue
                nueva = vigente_desde_archivo(nombre)
                if destino.exists() and destino.read_text() == nueva:
                    print(f"✓ {nombre}: la vigente ya está al día")
                else:
                    destino.write_text(nueva)
                    print(f"✓ {nombre}: vigente rearmada desde la versión del {publicadas[0][0]}")
                continue

            if a.verificar:
                if not destino.exists():
                    print(f"✗ {nombre}: {destino.relative_to(RAIZ)} no existe")
                    fallo = True
                    continue
                actual = destino.read_text()
                if not publicadas:
                    _, pagina, commit, _ = armar(nombre, False, None)
                    if sin_commit(actual) == sin_commit(pagina):
                        print(f"✓ {nombre}: borrador al día con {REFERENCIA} ({commit})")
                    else:
                        print(f"✗ {nombre}: el borrador NO coincide con {REFERENCIA} ({commit}) "
                              "— volver a construir")
                        fallo = True
                    continue
                # Publicado: son dos preguntas distintas y se contestan por separado.
                fecha, rige = publicadas[0]
                if actual == vigente_desde_archivo(nombre):
                    print(f"✓ {nombre}: la vigente muestra la versión del {fecha} con la línea correcta para hoy")
                else:
                    print(f"✗ {nombre}: la vigente no coincide con la versión del {fecha} "
                          "(¿venció un aviso?) — correr --refrescar")
                    fallo = True
                archivo = (destino.parent / fecha / "index.html").read_text()
                _, desde_fuente, commit, _ = armar(nombre, True, fecha, linea_archivo(nombre, fecha, rige),
                                                   estado="archivo", rige=rige)
                if sin_commit(archivo) == sin_commit(desde_fuente):
                    print(f"✓ {nombre}: la versión del {fecha} coincide con {REFERENCIA} ({commit})")
                else:
                    print(f"• {nombre}: la fuente cambió desde la versión del {fecha} ({REFERENCIA} {commit}) "
                          "— hay texto nuevo para publicar como versión nueva")
                continue

            ruta, pagina, commit, avisos = armar(nombre, False, None)
        except Rechazo as e:
            print(f"✗ {e}", file=sys.stderr)
            fallo = True
            continue
        for aviso in avisos:
            print(f"  ⚠ {nombre} — marca, avisar a legales: {aviso}", file=sys.stderr)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(pagina)
        print(f"✓ {nombre}: {ruta}  (borrador, fuente {commit})")

    sys.exit(1 if fallo else 0)


if __name__ == "__main__":
    main()
