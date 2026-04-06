# Initial Seed Blueprint

This document defines the initial coherent dataset for categories, products, colors, wood types, BOM recipes, and fabrication cost inputs used by the system seeds.

_Generated from scripts/seed_dataset.py on 2026-04-05._

> Official image sources for seeds:
> - Product gallery images (`product_images`): `docs/imagenes.csv`
> - Furniture type catalog images (`furniture_types.image_url`): `docs/Muebles.sql`

## 1. Category Catalog (13)

| Category | Slug | Target products | Official image |
| --- | --- | ---: | --- |
| Salas | salas | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775455612/furniture_types/fnvecygfqpm0rpyqn6rx.jpg |
| Comedores | comedores | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775458010/furniture_types/ouqralxg3gka1vgoxfq2.jpg |
| Recamaras | recamaras | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775496224/furniture_types/rsnhg0laxdefmgqcetfc.jpg |
| Closets y almacenamiento | closets-y-almacenamiento | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497577/furniture_types/tnuyy180ihuilnokvekd.jpg |
| Escritorios y oficina | escritorios-y-oficina | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497934/furniture_types/aw7rypycaeo6fmtp290i.jpg |
| Muebles para TV | muebles-para-tv | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775497993/furniture_types/cr82qzc2ujersa886ter.jpg |
| Mesas | mesas | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775498363/furniture_types/wpwoi4c898exi0iovggo.jpg |
| Estanterias y libreros | estanterias-y-libreros | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499187/furniture_types/rzn5lp82hzv0iqhg77s0.jpg |
| Cocina | cocina | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499233/furniture_types/rdflrqcsbcydjt7kanzc.jpg |
| Muebles infantiles | muebles-infantiles | 5 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775499784/furniture_types/er3lzioxzajmuz229d9x.jpg |
| Muebles decorativos | muebles-decorativos | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500157/furniture_types/kuswchaxjcb9qybe67kc.jpg |
| Muebles personalizados | muebles-personalizados | 0 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500499/furniture_types/yst2uo1nbpipfrvioijs.jpg |
| Muebles de jardin | muebles-de-jardin | 4 | https://res.cloudinary.com/dv26xoo6n/image/upload/v1775500555/furniture_types/s067dw7s6gr5xuyrubpg.jpg |

## 2. Global Catalog Inputs

### 2.1 Base colors

| Color | Hex |
| --- | --- |
| Blanco Hueso | #F6F2E9 |
| Negro Carbon | #1B1B1D |
| Gris Ceniza | #8D939A |
| Grafito | #4A4F57 |
| Beige Arena | #D7C4A3 |
| Azul Marino | #1E3A8A |
| Verde Oliva | #6A7A45 |
| Terracota | #B95D3C |
| Nogal Medio | #7A5237 |
| Roble Natural | #B08962 |

### 2.2 Wood types (catalog)

| Wood type | Description |
| --- | --- |
| Pino | Madera suave y versatil para estructuras interiores |
| Encino | Madera dura con veta fina para piezas premium |
| Parota | Madera tropical de veta marcada para muebles decorativos |
| Roble | Madera resistente para cubiertas y mesas de alto uso |
| Nogal | Madera oscura para acabados elegantes |
| Tzalam | Madera tropical para exterior y ambientes humedos |
| MDF | Tablero de fibra de densidad media para mobiliario modular |
| Triplay | Tablero multicapa para frentes y refuerzos |

### 2.3 Raw materials and purchase prices

| Raw material | Category | Unit | Waste % | Initial stock | Unit price |
| --- | --- | --- | ---: | ---: | ---: |
| Tablero MDF 15mm | Maderas | Pieza | 8.00 | 140.000 | 520.00 |
| Triplay Encino 18mm | Maderas | Pieza | 9.00 | 95.000 | 780.00 |
| Triplay Pino 15mm | Maderas | Pieza | 7.00 | 110.000 | 430.00 |
| Madera solida Encino 1x4 | Maderas | Metro lineal | 6.00 | 820.000 | 95.00 |
| Madera solida Parota 1x8 | Maderas | Metro lineal | 8.50 | 470.000 | 180.00 |
| Madera solida Tzalam 1x4 | Maderas | Metro lineal | 7.50 | 360.000 | 130.00 |
| Liston de Pino 2x2 | Maderas | Metro lineal | 5.50 | 980.000 | 48.00 |
| Cubierta alistonada Roble 30mm | Maderas | Pieza | 7.00 | 65.000 | 1250.00 |
| Corredera telescopica 45cm | Herrajes | Pieza | 1.50 | 760.000 | 68.00 |
| Bisagra cazoleta cierre suave | Herrajes | Pieza | 1.20 | 1900.000 | 34.00 |
| Tornillo confirmat 7x50 | Herrajes | Pieza | 2.00 | 38000.000 | 1.90 |
| Tornillo madera 1 1/4 | Herrajes | Pieza | 2.50 | 42000.000 | 1.10 |
| Tornillo inox exterior 1 1/4 | Herrajes | Pieza | 1.80 | 12000.000 | 2.40 |
| Jaladera aluminio 128mm | Herrajes | Pieza | 1.00 | 1400.000 | 42.00 |
| Escuadra metalica 2in | Herrajes | Pieza | 1.50 | 2200.000 | 18.00 |
| Herraje elevable mesa centro | Herrajes | Pieza | 1.00 | 220.000 | 220.00 |
| Rueda giratoria industrial 2in | Herrajes | Pieza | 1.00 | 500.000 | 55.00 |
| Barniz poliuretano mate | Acabados | Litro | 6.00 | 185.000 | 185.00 |
| Sellador nitrocelulosa | Acabados | Litro | 6.50 | 145.000 | 160.00 |
| Tinta base agua nogal | Acabados | Litro | 5.00 | 90.000 | 140.00 |
| Laca blanca semimate | Acabados | Litro | 6.00 | 165.000 | 178.00 |
| Barniz marino exterior | Acabados | Litro | 7.00 | 130.000 | 210.00 |
| Tela lino gris | Tapiceria y rellenos | Metro lineal | 4.00 | 420.000 | 95.00 |
| Tela poliester azul | Tapiceria y rellenos | Metro lineal | 4.50 | 260.000 | 88.00 |
| Espuma alta densidad 27kg | Tapiceria y rellenos | Pieza | 3.50 | 520.000 | 240.00 |
| Resorte zig-zag asiento | Tapiceria y rellenos | Pieza | 2.00 | 4400.000 | 14.00 |
| Correa elastica tapiceria | Tapiceria y rellenos | Metro lineal | 3.00 | 860.000 | 22.00 |
| Rattan sintetico exterior | Tapiceria y rellenos | Metro lineal | 4.00 | 640.000 | 65.00 |

## 3. Product Catalog by Category

Each product row references:
- `wood_type`: educational catalog reference (no FK on `products` in this phase).
- `color_palette`: deterministic color assignment for `product_colors`.
- `bom_template`: BOM template applied by `scripts/seed_bom.py` (version `v1`).

### Salas

- Subtitle: Sofas, loveseats, sillones y ottomanes
- Slug: salas
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| SA-001 | Sofa modular Nube | 15400.00 | Pino | Gris Ceniza, Beige Arena, Azul Marino | SOFA_3P |
| SA-002 | Sofa 3 plazas Lino | 14750.00 | Pino | Beige Arena, Gris Ceniza, Nogal Medio | SOFA_3P |
| SA-003 | Love seat Aurora | 11200.00 | Pino | Azul Marino, Gris Ceniza, Grafito | LOVE_SEAT |
| SA-004 | Sillon accent Oslo | 8450.00 | Pino | Azul Marino, Terracota, Beige Arena | SILLON_ACCENT |
| SA-005 | Ottoman Terra | 3950.00 | Pino | Terracota, Beige Arena, Gris Ceniza | OTTOMAN |

### Comedores

- Subtitle: Mesas de comedor, sillas, bancos y vitrinas
- Slug: comedores
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| CO-001 | Mesa comedor Roble 6P | 12400.00 | Roble | Roble Natural, Nogal Medio, Negro Carbon | MESA_COMEDOR |
| CO-002 | Mesa comedor extensible 8P | 15800.00 | Roble | Roble Natural, Nogal Medio, Blanco Hueso | MESA_COMEDOR_EXTENSIBLE |
| CO-003 | Silla comedor Nido | 2850.00 | Encino | Beige Arena, Gris Ceniza, Negro Carbon | SILLA_COMEDOR |
| CO-004 | Banco comedor Recto | 4200.00 | Encino | Beige Arena, Nogal Medio, Grafito | BANCO_COMEDOR |
| CO-005 | Vitrina comedor Verona | 13800.00 | MDF | Blanco Hueso, Roble Natural, Grafito | VITRINA_COMEDOR |

### Recamaras

- Subtitle: Camas, buros, comodas y cabeceras
- Slug: recamaras
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| RE-001 | Cama Queen Horizonte | 16900.00 | Triplay | Beige Arena, Gris Ceniza, Nogal Medio | CAMA_QUEEN |
| RE-002 | Cama King Brisa | 19800.00 | Triplay | Beige Arena, Azul Marino, Gris Ceniza | CAMA_KING |
| RE-003 | Buro Flotante Duo | 3150.00 | MDF | Blanco Hueso, Nogal Medio, Grafito | BURO |
| RE-004 | Comoda 6 cajones Alba | 9800.00 | MDF | Blanco Hueso, Grafito, Roble Natural | COMODA |
| RE-005 | Cabecera tapizada Siena | 7600.00 | Pino | Beige Arena, Azul Marino, Terracota | CABECERA |

### Closets y almacenamiento

- Subtitle: Closets, roperos y organizadores
- Slug: closets-y-almacenamiento
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| CL-001 | Closet 2 puertas Nova | 12200.00 | MDF | Blanco Hueso, Roble Natural, Grafito | CLOSET_2P |
| CL-002 | Ropero 3 puertas Atena | 15900.00 | MDF | Blanco Hueso, Nogal Medio, Grafito | ROPERO_3P |
| CL-003 | Organizador modular Cubos | 5600.00 | MDF | Blanco Hueso, Roble Natural, Verde Oliva | ORGANIZADOR_CUBOS |
| CL-004 | Zapatera vertical Lumo | 6200.00 | MDF | Blanco Hueso, Nogal Medio, Negro Carbon | ZAPATERA |

### Escritorios y oficina

- Subtitle: Escritorios, credenzas y muebles para home office
- Slug: escritorios-y-oficina
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| OF-001 | Escritorio recto Focus | 6900.00 | Encino | Roble Natural, Nogal Medio, Negro Carbon | ESCRITORIO_RECTO |
| OF-002 | Escritorio en L Vector | 9200.00 | Encino | Roble Natural, Grafito, Blanco Hueso | ESCRITORIO_L |
| OF-003 | Escritorio elevable Shift | 11400.00 | Encino | Blanco Hueso, Negro Carbon, Roble Natural | ESCRITORIO_ELEVABLE |
| OF-004 | Credenza oficina Axis | 8450.00 | MDF | Grafito, Blanco Hueso, Nogal Medio | CREDENZA |
| OF-005 | Librero oficina Grid | 7200.00 | MDF | Roble Natural, Grafito, Blanco Hueso | LIBRERO_OFICINA |

### Muebles para TV

- Subtitle: Centros de entretenimiento y consolas multimedia
- Slug: muebles-para-tv
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| TV-001 | Centro TV Orion 65 | 9800.00 | MDF | Grafito, Roble Natural, Blanco Hueso | CENTRO_TV |
| TV-002 | Mueble TV Minimal 55 | 7900.00 | MDF | Blanco Hueso, Nogal Medio, Negro Carbon | MUEBLE_TV |
| TV-003 | Consola multimedia Delta | 6950.00 | Encino | Roble Natural, Nogal Medio, Grafito | CONSOLA_MEDIA |
| TV-004 | Panel TV suspendido Linea | 5600.00 | MDF | Blanco Hueso, Grafito, Roble Natural | PANEL_TV |

### Mesas

- Subtitle: Mesas de centro, laterales, auxiliares y recibidor
- Slug: mesas
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| ME-001 | Mesa de centro Duela | 6200.00 | Roble | Roble Natural, Nogal Medio, Negro Carbon | MESA_CENTRO |
| ME-002 | Mesa lateral Nido | 2950.00 | Parota | Nogal Medio, Roble Natural, Negro Carbon | MESA_LATERAL |
| ME-003 | Mesa auxiliar C | 2550.00 | Encino | Blanco Hueso, Roble Natural, Grafito | MESA_AUXILIAR_C |
| ME-004 | Mesa centro elevable Loft | 7400.00 | Encino | Roble Natural, Grafito, Blanco Hueso | MESA_CENTRO_ELEVABLE |
| ME-005 | Mesa de recibidor Halo | 4850.00 | Parota | Nogal Medio, Terracota, Negro Carbon | MESA_RECIBIDOR |

### Estanterias y libreros

- Subtitle: Libreros, estantes, repisas y modulares
- Slug: estanterias-y-libreros
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| LI-001 | Librero 5 niveles Nara | 7100.00 | MDF | Roble Natural, Grafito, Blanco Hueso | LIBRERO_5N |
| LI-002 | Estante escalera Pino | 4900.00 | Pino | Roble Natural, Verde Oliva, Blanco Hueso | ESTANTE_ESCALERA |
| LI-003 | Repisa flotante Set 3 | 2100.00 | Encino | Roble Natural, Nogal Medio, Blanco Hueso | REPISA_SET |
| LI-004 | Librero bajo Compacto | 4300.00 | MDF | Blanco Hueso, Grafito, Roble Natural | LIBRERO_BAJO |

### Cocina

- Subtitle: Alacenas, islas y gabinetes
- Slug: cocina
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| KC-001 | Isla de cocina Moka | 13200.00 | MDF | Blanco Hueso, Roble Natural, Grafito | ISLA_COCINA |
| KC-002 | Alacena alto brillo | 11800.00 | MDF | Blanco Hueso, Grafito, Nogal Medio | ALACENA |
| KC-003 | Gabinete base fregadero | 8600.00 | MDF | Blanco Hueso, Grafito, Roble Natural | GABINETE_BASE |
| KC-004 | Carro auxiliar Chef | 5400.00 | MDF | Blanco Hueso, Roble Natural, Terracota | CARRO_AUXILIAR |

### Muebles infantiles

- Subtitle: Camas, escritorios y organizadores para ninos
- Slug: muebles-infantiles
- Target products: 5

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| IN-001 | Cama Montessori Luna | 6900.00 | Pino | Blanco Hueso, Roble Natural, Terracota | CAMA_MONTESSORI |
| IN-002 | Escritorio infantil Pixel | 3950.00 | Pino | Blanco Hueso, Azul Marino, Verde Oliva | ESCRITORIO_INFANTIL |
| IN-003 | Librero infantil Casa | 3600.00 | MDF | Blanco Hueso, Terracota, Verde Oliva | LIBRERO_INFANTIL |
| IN-004 | Organizador juguetes Arco | 3250.00 | MDF | Blanco Hueso, Azul Marino, Terracota | ORGANIZADOR_JUGUETES |
| IN-005 | Buro infantil Estrella | 2550.00 | MDF | Blanco Hueso, Azul Marino, Verde Oliva | BURO_INFANTIL |

### Muebles decorativos

- Subtitle: Consolas, biombos y bancos decorativos
- Slug: muebles-decorativos
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| DE-001 | Consola entrada Marmol | 8400.00 | Parota | Nogal Medio, Negro Carbon, Blanco Hueso | CONSOLA_DECORATIVA |
| DE-002 | Biombo madera Trama | 6100.00 | Parota | Nogal Medio, Terracota, Azul Marino | BIOMBO |
| DE-003 | Banco decorativo Trenza | 4700.00 | Encino | Beige Arena, Terracota, Grafito | BANCO_DECORATIVO |
| DE-004 | Mesa consola Curva | 6900.00 | Parota | Nogal Medio, Roble Natural, Negro Carbon | MESA_CONSOLA_CURVA |

### Muebles personalizados

- Subtitle: Diseno a medida y proyectos especiales bajo pedido
- Slug: muebles-personalizados
- Target products: 0

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| - | No initial products by design | - | - | - | - |

### Muebles de jardin

- Subtitle: Salas, comedores y descanso para exterior
- Slug: muebles-de-jardin
- Target products: 4

| SKU | Product | Price | Wood type | Color palette | BOM template |
| --- | --- | ---: | --- | --- | --- |
| JA-001 | Sala exterior Palma | 18900.00 | Tzalam | Beige Arena, Grafito, Verde Oliva | SALA_EXTERIOR |
| JA-002 | Comedor exterior Brisa | 21400.00 | Tzalam | Roble Natural, Grafito, Verde Oliva | COMEDOR_EXTERIOR |
| JA-003 | Camastro ajustable Sol | 9900.00 | Tzalam | Beige Arena, Azul Marino, Grafito | CAMASTRO |
| JA-004 | Banco jardin Terraza | 5600.00 | Tzalam | Roble Natural, Verde Oliva, Grafito | BANCO_EXTERIOR |

## 4. BOM Templates

The following templates are reused across products and are resolved to real `raw_material_id` values at seed time.

### ALACENA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 2.100 |
| Bisagra cazoleta cierre suave | 6.000 |
| Jaladera aluminio 128mm | 4.000 |
| Tornillo confirmat 7x50 | 32.000 |
| Laca blanca semimate | 0.420 |

### BANCO_COMEDOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Encino 1x4 | 5.500 |
| Triplay Pino 15mm | 0.450 |
| Tela lino gris | 1.600 |
| Espuma alta densidad 27kg | 0.700 |
| Tornillo madera 1 1/4 | 18.000 |
| Barniz poliuretano mate | 0.150 |

### BANCO_DECORATIVO

| Raw material | Qty required |
| --- | ---: |
| Madera solida Encino 1x4 | 3.900 |
| Tela lino gris | 1.500 |
| Espuma alta densidad 27kg | 0.600 |
| Tornillo madera 1 1/4 | 14.000 |
| Barniz poliuretano mate | 0.140 |

### BANCO_EXTERIOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Tzalam 1x4 | 8.000 |
| Tornillo inox exterior 1 1/4 | 18.000 |
| Barniz marino exterior | 0.360 |

### BIOMBO

| Raw material | Qty required |
| --- | ---: |
| Madera solida Parota 1x8 | 3.200 |
| Tela poliester azul | 2.400 |
| Tornillo madera 1 1/4 | 18.000 |
| Barniz poliuretano mate | 0.180 |

### BURO

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.550 |
| Corredera telescopica 45cm | 2.000 |
| Jaladera aluminio 128mm | 1.000 |
| Tornillo confirmat 7x50 | 14.000 |
| Laca blanca semimate | 0.160 |

### BURO_INFANTIL

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.500 |
| Corredera telescopica 45cm | 2.000 |
| Jaladera aluminio 128mm | 1.000 |
| Tornillo confirmat 7x50 | 10.000 |
| Laca blanca semimate | 0.130 |

### CABECERA

| Raw material | Qty required |
| --- | ---: |
| Triplay Pino 15mm | 0.900 |
| Tela lino gris | 2.200 |
| Espuma alta densidad 27kg | 0.900 |
| Correa elastica tapiceria | 3.000 |
| Tornillo madera 1 1/4 | 12.000 |

### CAMASTRO

| Raw material | Qty required |
| --- | ---: |
| Madera solida Tzalam 1x4 | 11.000 |
| Rattan sintetico exterior | 6.500 |
| Tornillo inox exterior 1 1/4 | 24.000 |
| Barniz marino exterior | 0.500 |

### CAMA_KING

| Raw material | Qty required |
| --- | ---: |
| Triplay Encino 18mm | 1.850 |
| Liston de Pino 2x2 | 18.000 |
| Tela lino gris | 2.300 |
| Espuma alta densidad 27kg | 1.100 |
| Tornillo confirmat 7x50 | 32.000 |
| Barniz poliuretano mate | 0.420 |

### CAMA_MONTESSORI

| Raw material | Qty required |
| --- | ---: |
| Triplay Pino 15mm | 1.200 |
| Liston de Pino 2x2 | 8.500 |
| Tornillo madera 1 1/4 | 20.000 |
| Laca blanca semimate | 0.240 |
| Sellador nitrocelulosa | 0.170 |

### CAMA_QUEEN

| Raw material | Qty required |
| --- | ---: |
| Triplay Encino 18mm | 1.450 |
| Liston de Pino 2x2 | 14.000 |
| Tela lino gris | 1.900 |
| Espuma alta densidad 27kg | 0.900 |
| Tornillo confirmat 7x50 | 26.000 |
| Barniz poliuretano mate | 0.350 |

### CARRO_AUXILIAR

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.950 |
| Rueda giratoria industrial 2in | 4.000 |
| Tornillo confirmat 7x50 | 16.000 |
| Laca blanca semimate | 0.180 |

### CENTRO_TV

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.900 |
| Triplay Encino 18mm | 0.650 |
| Corredera telescopica 45cm | 2.000 |
| Bisagra cazoleta cierre suave | 2.000 |
| Tornillo confirmat 7x50 | 28.000 |
| Laca blanca semimate | 0.330 |

### CLOSET_2P

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 2.500 |
| Triplay Pino 15mm | 0.900 |
| Bisagra cazoleta cierre suave | 4.000 |
| Jaladera aluminio 128mm | 2.000 |
| Tornillo confirmat 7x50 | 36.000 |
| Laca blanca semimate | 0.420 |

### COMEDOR_EXTERIOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Tzalam 1x4 | 18.000 |
| Rattan sintetico exterior | 7.000 |
| Tornillo inox exterior 1 1/4 | 34.000 |
| Barniz marino exterior | 0.680 |

### COMODA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.650 |
| Corredera telescopica 45cm | 6.000 |
| Jaladera aluminio 128mm | 6.000 |
| Tornillo confirmat 7x50 | 30.000 |
| Laca blanca semimate | 0.450 |
| Sellador nitrocelulosa | 0.300 |

### CONSOLA_DECORATIVA

| Raw material | Qty required |
| --- | ---: |
| Madera solida Parota 1x8 | 4.100 |
| Escuadra metalica 2in | 4.000 |
| Tornillo madera 1 1/4 | 16.000 |
| Tinta base agua nogal | 0.150 |
| Barniz poliuretano mate | 0.220 |

### CONSOLA_MEDIA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.350 |
| Madera solida Encino 1x4 | 3.200 |
| Tornillo confirmat 7x50 | 18.000 |
| Escuadra metalica 2in | 4.000 |
| Barniz poliuretano mate | 0.220 |

### CREDENZA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.800 |
| Corredera telescopica 45cm | 4.000 |
| Jaladera aluminio 128mm | 4.000 |
| Tornillo confirmat 7x50 | 28.000 |
| Laca blanca semimate | 0.350 |

### ESCRITORIO_ELEVABLE

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.500 |
| Madera solida Encino 1x4 | 5.500 |
| Herraje elevable mesa centro | 1.000 |
| Tornillo confirmat 7x50 | 24.000 |
| Barniz poliuretano mate | 0.280 |

### ESCRITORIO_INFANTIL

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.850 |
| Liston de Pino 2x2 | 3.800 |
| Tornillo madera 1 1/4 | 14.000 |
| Laca blanca semimate | 0.180 |

### ESCRITORIO_L

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.900 |
| Madera solida Encino 1x4 | 6.200 |
| Tornillo confirmat 7x50 | 30.000 |
| Escuadra metalica 2in | 6.000 |
| Barniz poliuretano mate | 0.320 |

### ESCRITORIO_RECTO

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.300 |
| Madera solida Encino 1x4 | 4.500 |
| Tornillo confirmat 7x50 | 22.000 |
| Escuadra metalica 2in | 4.000 |
| Barniz poliuretano mate | 0.240 |

### ESTANTE_ESCALERA

| Raw material | Qty required |
| --- | ---: |
| Madera solida Encino 1x4 | 5.000 |
| Tablero MDF 15mm | 0.700 |
| Tornillo madera 1 1/4 | 18.000 |
| Barniz poliuretano mate | 0.220 |

### GABINETE_BASE

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.700 |
| Triplay Pino 15mm | 0.450 |
| Bisagra cazoleta cierre suave | 2.000 |
| Jaladera aluminio 128mm | 2.000 |
| Tornillo confirmat 7x50 | 24.000 |
| Laca blanca semimate | 0.300 |

### ISLA_COCINA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 2.600 |
| Triplay Encino 18mm | 0.900 |
| Rueda giratoria industrial 2in | 4.000 |
| Jaladera aluminio 128mm | 2.000 |
| Tornillo confirmat 7x50 | 34.000 |
| Laca blanca semimate | 0.500 |

### LIBRERO_5N

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.800 |
| Triplay Pino 15mm | 0.650 |
| Tornillo confirmat 7x50 | 24.000 |
| Barniz poliuretano mate | 0.260 |
| Sellador nitrocelulosa | 0.200 |

### LIBRERO_BAJO

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.200 |
| Triplay Pino 15mm | 0.400 |
| Tornillo confirmat 7x50 | 16.000 |
| Laca blanca semimate | 0.220 |

### LIBRERO_INFANTIL

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.950 |
| Triplay Pino 15mm | 0.300 |
| Tornillo confirmat 7x50 | 12.000 |
| Laca blanca semimate | 0.170 |

### LIBRERO_OFICINA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.700 |
| Triplay Pino 15mm | 0.550 |
| Tornillo confirmat 7x50 | 20.000 |
| Barniz poliuretano mate | 0.260 |
| Sellador nitrocelulosa | 0.180 |

### LOVE_SEAT

| Raw material | Qty required |
| --- | ---: |
| Liston de Pino 2x2 | 12.000 |
| Tela lino gris | 4.800 |
| Espuma alta densidad 27kg | 2.800 |
| Resorte zig-zag asiento | 8.000 |
| Correa elastica tapiceria | 7.000 |
| Tornillo madera 1 1/4 | 28.000 |
| Barniz poliuretano mate | 0.420 |

### MESA_AUXILIAR_C

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 0.500 |
| Madera solida Encino 1x4 | 2.800 |
| Tornillo madera 1 1/4 | 10.000 |
| Barniz poliuretano mate | 0.120 |

### MESA_CENTRO

| Raw material | Qty required |
| --- | ---: |
| Cubierta alistonada Roble 30mm | 0.650 |
| Madera solida Encino 1x4 | 4.500 |
| Tornillo madera 1 1/4 | 16.000 |
| Barniz poliuretano mate | 0.220 |
| Sellador nitrocelulosa | 0.160 |

### MESA_CENTRO_ELEVABLE

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.050 |
| Madera solida Encino 1x4 | 3.800 |
| Herraje elevable mesa centro | 1.000 |
| Tornillo confirmat 7x50 | 20.000 |
| Barniz poliuretano mate | 0.200 |

### MESA_COMEDOR

| Raw material | Qty required |
| --- | ---: |
| Cubierta alistonada Roble 30mm | 1.000 |
| Madera solida Encino 1x4 | 10.000 |
| Escuadra metalica 2in | 8.000 |
| Tornillo confirmat 7x50 | 24.000 |
| Barniz poliuretano mate | 0.500 |
| Sellador nitrocelulosa | 0.350 |

### MESA_COMEDOR_EXTENSIBLE

| Raw material | Qty required |
| --- | ---: |
| Cubierta alistonada Roble 30mm | 1.350 |
| Madera solida Encino 1x4 | 13.000 |
| Escuadra metalica 2in | 10.000 |
| Tornillo confirmat 7x50 | 32.000 |
| Barniz poliuretano mate | 0.620 |
| Sellador nitrocelulosa | 0.420 |

### MESA_CONSOLA_CURVA

| Raw material | Qty required |
| --- | ---: |
| Madera solida Parota 1x8 | 3.600 |
| Madera solida Encino 1x4 | 2.000 |
| Tornillo madera 1 1/4 | 15.000 |
| Barniz poliuretano mate | 0.200 |

### MESA_LATERAL

| Raw material | Qty required |
| --- | ---: |
| Madera solida Parota 1x8 | 2.500 |
| Tornillo madera 1 1/4 | 12.000 |
| Escuadra metalica 2in | 3.000 |
| Barniz poliuretano mate | 0.150 |

### MESA_RECIBIDOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Parota 1x8 | 3.600 |
| Escuadra metalica 2in | 4.000 |
| Tornillo madera 1 1/4 | 14.000 |
| Tinta base agua nogal | 0.120 |
| Barniz poliuretano mate | 0.180 |

### MUEBLE_TV

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.500 |
| Triplay Encino 18mm | 0.500 |
| Tornillo confirmat 7x50 | 22.000 |
| Jaladera aluminio 128mm | 2.000 |
| Laca blanca semimate | 0.250 |

### ORGANIZADOR_CUBOS

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.250 |
| Tornillo confirmat 7x50 | 20.000 |
| Escuadra metalica 2in | 6.000 |
| Laca blanca semimate | 0.260 |
| Sellador nitrocelulosa | 0.180 |

### ORGANIZADOR_JUGUETES

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.100 |
| Rueda giratoria industrial 2in | 4.000 |
| Tornillo confirmat 7x50 | 14.000 |
| Laca blanca semimate | 0.190 |

### OTTOMAN

| Raw material | Qty required |
| --- | ---: |
| Triplay Pino 15mm | 0.350 |
| Tela lino gris | 1.400 |
| Espuma alta densidad 27kg | 0.900 |
| Correa elastica tapiceria | 2.000 |
| Tornillo madera 1 1/4 | 12.000 |
| Barniz poliuretano mate | 0.080 |

### PANEL_TV

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.200 |
| Escuadra metalica 2in | 6.000 |
| Tornillo confirmat 7x50 | 14.000 |
| Laca blanca semimate | 0.220 |

### REPISA_SET

| Raw material | Qty required |
| --- | ---: |
| Madera solida Encino 1x4 | 2.800 |
| Escuadra metalica 2in | 6.000 |
| Tornillo madera 1 1/4 | 12.000 |
| Barniz poliuretano mate | 0.100 |

### ROPERO_3P

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 3.600 |
| Triplay Pino 15mm | 1.100 |
| Bisagra cazoleta cierre suave | 6.000 |
| Jaladera aluminio 128mm | 3.000 |
| Tornillo confirmat 7x50 | 48.000 |
| Laca blanca semimate | 0.580 |

### SALA_EXTERIOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Tzalam 1x4 | 16.000 |
| Rattan sintetico exterior | 10.000 |
| Espuma alta densidad 27kg | 3.000 |
| Tornillo inox exterior 1 1/4 | 30.000 |
| Barniz marino exterior | 0.620 |

### SILLA_COMEDOR

| Raw material | Qty required |
| --- | ---: |
| Madera solida Encino 1x4 | 4.200 |
| Triplay Encino 18mm | 0.280 |
| Tela lino gris | 0.850 |
| Espuma alta densidad 27kg | 0.300 |
| Tornillo madera 1 1/4 | 14.000 |
| Barniz poliuretano mate | 0.120 |

### SILLON_ACCENT

| Raw material | Qty required |
| --- | ---: |
| Liston de Pino 2x2 | 9.000 |
| Tela poliester azul | 3.200 |
| Espuma alta densidad 27kg | 2.000 |
| Resorte zig-zag asiento | 6.000 |
| Correa elastica tapiceria | 5.000 |
| Tornillo madera 1 1/4 | 22.000 |
| Barniz poliuretano mate | 0.300 |

### SOFA_3P

| Raw material | Qty required |
| --- | ---: |
| Liston de Pino 2x2 | 18.000 |
| Tela lino gris | 7.000 |
| Espuma alta densidad 27kg | 4.000 |
| Resorte zig-zag asiento | 12.000 |
| Correa elastica tapiceria | 10.000 |
| Tornillo madera 1 1/4 | 42.000 |
| Barniz poliuretano mate | 0.600 |

### VITRINA_COMEDOR

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.850 |
| Triplay Encino 18mm | 0.750 |
| Bisagra cazoleta cierre suave | 6.000 |
| Jaladera aluminio 128mm | 4.000 |
| Tornillo confirmat 7x50 | 30.000 |
| Laca blanca semimate | 0.420 |

### ZAPATERA

| Raw material | Qty required |
| --- | ---: |
| Tablero MDF 15mm | 1.500 |
| Bisagra cazoleta cierre suave | 4.000 |
| Jaladera aluminio 128mm | 2.000 |
| Tornillo confirmat 7x50 | 24.000 |
| Laca blanca semimate | 0.300 |

## 5. Seed Execution Order

1. `venv/bin/python scripts/seed_units.py`
2. `venv/bin/python scripts/seed_raw_materials.py`
3. `venv/bin/python scripts/seed_wood_types.py`
4. `venv/bin/python scripts/seed_products.py`
5. `venv/bin/python scripts/seed_product_colors.py`
6. `venv/bin/python scripts/seed_purchase.py`
7. `venv/bin/python scripts/seed_bom.py`
8. `venv/bin/python scripts/seed_inventory.py`

## 6. Coherence Rules

- 13 active furniture categories are seeded with image URLs.
- 12 categories contain 4-5 products each; `Muebles personalizados` intentionally has 0 products.
- Every seeded product includes deterministic colors, wood type reference, and BOM template.
- Every BOM template uses raw materials that receive purchase prices so fabrication cost is calculable.
- Seeds are idempotent by upsert/update strategy and can be rerun safely in development.
