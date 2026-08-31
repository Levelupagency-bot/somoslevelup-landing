# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primario:** dueños de negocios de **alto ticket** en el interior argentino — concesionarias (vertical de ataque), maquinaria agrícola e industrial, inmobiliarias, energía solar. Ya venden, tienen equipo de 2 a 5 personas y reciben consultas todas las semanas. Sospechan que se les caen ventas por falta de seguimiento, pero no lo pueden probar: no pueden reconstruir qué pasó con una consulta puntual.

**Situación de uso:** el dueño mira desde el celular, muchas veces entre otra cosa. No es un comprador de software; es alguien que decide una inversión para su negocio y quiere saber si el que está del otro lado es serio.

**El trabajo que viene a hacer:** decidir si vale la pena tener una conversación. No comparar features.

**Quién decide:** el dueño. Si no está él en la reunión, no hay reunión (es criterio de calificación explícito).

## Product Purpose

Level Up construye **infraestructura comercial**: el sistema por el que toda consulta entra a un solo lugar, se asigna a un responsable, se sigue y queda registrada con su origen, su tiempo de respuesta y su próximo paso.

**Qué es el éxito para la web:** que el visitante calificado pida la sesión de diagnóstico de 45 minutos. Es el único CTA.

**Qué es el éxito para el producto:** que el dueño pueda contestar "¿qué pasó con cada consulta del mes pasado?" — trazabilidad y tiempos, nunca ventas.

## Positioning

**Ingeniería comercial, nunca agencia.** Construye infraestructura, no hace marketing.

Lo que un competidor no puede copiar honestamente: Level Up **no promete ventas y lo dice en la cara**. Vende un entregable verificable que controla (orden, trazabilidad, tiempos de respuesta) y deja explícito que el cierre es del equipo del cliente. La captación va incluida pero se mide por consultas y costo por consulta, nunca por facturación.

El centro de la oferta es el **orden y la trazabilidad**, no el agente de IA. El agente (LIA) es un módulo incluido que se activa solo si el cliente lo quiere: los dos clientes reales del rubro no querían un bot.

## Operating Context

- Las consultas del cliente final llegan por WhatsApp, Instagram, Facebook, web y formularios de Meta Ads. El equipo del cliente contesta desde su propio celular y conserva su número de siempre.
- El ciclo de venta del cliente es largo: días o semanas de seguimiento por operación.
- **Una sola empresa por ciudad** — política, no precio. La prospección va fuera de Reconquista.
- El canal principal de Level Up son los **referidos** (8 de 8 clientes actuales). Los ads son un canal en construcción.
- Capacidad real: 2 implementaciones por mes. El cupo es verdadero, no un recurso de escasez.
- La sesión de 45 minutos la hace Nico en persona.

**Los cuatro trabajos de la web (confirmados por Nico):**
1. Conseguir la sesión — objetivo principal
2. Respaldar la propuesta: el prospecto la abre para verificar que la firma existe y es seria
3. Herramienta de referido: un cliente actual se la pasa a un conocido, y tiene que explicarse sola
4. Sitio oficial del negocio para trámites y verificación de Meta

**Tráfico:** mitad referido (llega tibio, ya confía) y mitad frío (ads e Instagram). La página tiene que servir a los dos sin romperse para ninguno.

## Capabilities and Constraints

- **Formulario intocable en su función:** POST JSON a `https://n8n.srv1035755.hstgr.cloud/webhook/e48fc3b6-eb6c-42d5-be1e-9e56a1fe25a1` con los campos `{nombre, email, whatsapp, rubro, problema}`. Es la captura de leads real. La estética se puede rediseñar; el envío no se rompe.
- Repo `Levelupagency-bot/somoslevelup-landing`, un solo `index.html` sin build, desplegado desde GitHub. Dominio somoslevelup.com.
- **Los precios no se publican.** Nunca, en ningún lado.
- **No se promete ningún resultado**: ni ventas, ni cantidad de consultas, ni facturación, ni retorno.
- Hay **una sola oferta**. No existe un plan más barato que mostrar.
- Terminología obligatoria: "sistema de gestión de clientes", nunca "CRM". "Evaluación", nunca "auditoría" (Level Up implementa y evalúa: no hay independencia, y Nico construye en paralelo una posición como auditor real).
- Separación de vocabulario innegociable: **"sesión"** = la instancia gratuita, una conversación de 45 minutos sin entregable. **"Radiografía Comercial™" / "evaluación"** = el trabajo pago, con informe de 5 páginas. Nunca cruzar los términos.
- Extras publicables: dos, Radiografía Comercial™ y capacitación de equipos comerciales. Ninguno se vende desde la web: ambos derivan a la sesión.
- CERO FUGAS™ (producto digital) va solo como mención discreta al final, lejos de la oferta principal.

## Brand Commitments

- Nombre: **Level Up™ | AIMA**. Reconquista, Santa Fe, Argentina. Instagram: https://www.instagram.com/levelup.aima/
- Vocabulario **siempre**: infraestructura · ingeniería · activo · trazabilidad · sistema · sistema de gestión de clientes.
- Vocabulario **nunca**: CRM · marketing digital · agencia · community manager · posteos · escalar · humo.
- Idioma: español rioplatense con voseo. Tono directo, sobrio, sin adulación y sin humo.
- Nada se publica sin aprobación explícita de Nico.

## Evidence on Hand

- **Caso real, único publicable:** dos concesionarias de Reconquista. 3 autos vendidos atribuibles al seguimiento en unos dos meses; la venta más larga llevó 30 días de seguimiento y el cliente nunca dijo que no. **Los nombres no están autorizados para uso público.** Sin cifras de retorno.
- **No existen** testimonios publicables, logos de clientes, ni métricas verificadas de retorno. Las que estaban en la web anterior ("3.2x", "+140%", "22 clientes") **no están verificadas y no se vuelven a publicar**.
- **Assets:** Nico declara tener material disponible (capturas del sistema real, fotos propias y del equipo, fotos de clientes e instalaciones) **pero prefiere que el material de la web sea nuevo, no reciclado.** → **Decisión abierta:** si el mundo visual necesita imágenes, hay que definir si se produce material nuevo o se resuelve gráficamente. No inventar assets que no existen.

## Product Principles

1. **La honestidad es el argumento de venta.** Decir lo que no se hace vende más que prometer. Si de la sesión sale que el problema no es el seguimiento, se dice y no se vende nada.
2. **El filtro es parte del producto.** No se trabaja con todos, y decirlo antes evita el problema a los dos meses.
3. **Todo empuja a una sola puerta.** La sesión es el único CTA; los extras se hablan adentro de esa reunión, no compiten en la página.
4. **Se mide lo que se controla.** Trazabilidad y tiempos para el sistema; consultas y costo por consulta para la captación. Las ventas se miran en la revisión trimestral, no en la promesa.
5. **La página tiene que aguantar dos miradas:** la del desconocido que llega frío y la del referido que ya confía y viene a confirmar que esto es serio.

## Accessibility & Inclusion

- **Mobile obligatorio y prioritario:** los dueños miran desde el celular, en condiciones de luz y atención variables. Ninguna decisión visual puede degradar esa lectura.
- Contraste y tamaños de texto legibles para un público de 35 a 55 años que no es early adopter de software.
- Respetar `prefers-reduced-motion` en cualquier movimiento.
