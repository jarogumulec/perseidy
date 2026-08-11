# Interaktivní mapa tmavých míst pro pozorování oblohy v ČR

## 🌌 Interaktivní mapa je online

 **https://jarogumulec.github.io/perseidy/**

Mapa představena v článku iROZHLAS.cz: *"Odkud sledovat Perseidy? Napoví mapa vyhlídkových míst s nejmenším světelným znečištěním"* (Petr Kočí, Michal Kašpárek)

---

Tento projekt vytváří interaktivní nástroj pro hledání optimálních lokalit v České republice pro pozorování Perseid a dalších meteorických rojů. Analýza kombinuje tři klíčové faktory:
- **Světelné znečištění** (Falchi et al. 2016 atlas) — jak světlá je obloha nad daným místem
- **Výhledová místa** z OpenStreetMap (rozhledny, vyhlídky, vrcholy) — kde skutečně vidíš na oblohu
- **Dostupnost** (izochrony dojezdu z krajských měst) — kam stihneš dojet za hodinu

Pro představu: v celé ČR existují stovky potenciálních lokalit, ale po filtrování podle světelného znečištění a dopravní dostupnosti zůstává každému regionu jen několik málo vhodných míst. Nejhorší situace je v okolí Prahy, kde se světlo ze města šíří desítky kilometrů a kvalitních lokalit je velmi omezený počet.

## Proč právě Falchi atlas? (i když data jsou z roku 2015)

Při výběru datasetu pro světelné znečištění jsme narazili na modernější alternativy jako VIIRS Black Marble nebo WorldPop. Zásadní rozdíl:

| Dataset | Co měří | Vhodné pro astronomy? |
|---------|---------|----------------------|
| **Falchi 2015** | Jas noční oblohy (skyglow) po atmosférickém rozptylu | ✅ ANO - přímo to, co vidíš nad hlavou |
| **VIIRS / Black Marble** | Světlo vycházející ze země směrem vzhůru | ❌ NE - ukazuje města/ulice, ne kvalitu oblohy |

Pro astronomii není podstatné kolik světla vychází ze zemského povrchu, ale jak světlá je obloha nad tebou. Mezi těmito dvěma veličinami leží atmosférický rozptyl - a právě ten Falchi modeluje.

I když jsou Falchi data z roku 2015, stále poskytují smysluplnější informaci pro výběr pozorovacích lokalit než aktuálnější VIIRS rastry. Relativní pořadí tmavých oblastí v ČR se za posledních 10 let významně nezměnilo.

## Datové zdroje

### Světelné znečištění
- **Zdroj**: Falchi et al., "The New World Atlas of Artificial Night Sky Brightness" (2016)
- **DOI**: [10.5880/GFZ.1.4.2016.001](https://doi.org/10.5880/GFZ.1.4.2016.001)
- **Jednotky**: Poměr k přirozenému jasu oblohy (0 = žádná umělá složka, >1 = jasnější než přirozené pozadí)
- **Citace**: Původní článek: [10.1126/sciadv.1600377](https://doi.org/10.1126/sciadv.1600377)

### Výhledová místa
- **Zdroj**: Michal Kašpárek / Data Rozhlas
- **Originální CSV**: [divnovylety/vyhlidkova_mista_cr.csv](https://github.com/DataRozhlas/divnovylety/blob/b74d0d606e967e6b8bc3e9ca77bc8ff908ac0b04/data/vyhlidkova_mista_cr.csv)
- **Extrahováno z**: OpenStreetMap přes Overpass API
- **Kategorie (astronomy strict)**: Pouze `tourism=viewpoint` a `natural=peak` — rozhledny (`man_made=observation_tower`) jsou vyřazeny protože mají světla uvnitř objektu
- **Čištění**: Původní data jsou kontaminovaná surveillance kamerami, webkamerami a dopravním značením. Pipeline nejprve odstraní zjevné nesmysly (`clean_viewpoints.py` → 5395 z 17521), pak aplikuje **astronomy strict** filtr pro pozorování oblohy (`clean_viewpoints_astronomy_strict.py` → 993 bodů).

### Izochrony
- **Zdroj**: OpenRouteService API
- **Profil**: Driving-car
- **Časový interval**: 1 hodina od každého krajského města

## Interaktivní mapy

Po spuštění `create_html_maps.py` najdeš v `output/` dvě hlavní varianty map:

| Soubor | Popis |
|--------|-------|
| `perseidy_regional.html` | Mapa ČR s vrstvami - zaškrtávací menu vlevo, legenda vpravo dole |
| `perseidy_full_cz.html` | Celá ČR s výhledovými místy - "najdi si svoje místo" |

**Bonusové mapy pro konkrétní lokality** (vytvořeny ručně přes `create_custom_location_maps.py`):
- `perseidy_brno.html` — Brno a okolí, s izochronami 15, 30, 45 a 60 minut

**Vlastnosti všech map:**
- **Layer control**: Zaškrtávací seznam vrstev (Světelné znečištění, Izochrony, Výhledová místa)
- **Legenda**: Kompaktní barevná škála Falchi vpravo dole

HTML mapy se generují do `output/`, pro GitHub Pages se pak kopírují do `docs/output/`:

| Cíl | Popis |
|-----|-------|
| `output/*.html` | Pracovní verze po generování |
| `docs/output/*.html` | Verze pro GitHub Pages (https://jarogumulec.github.io/perseidy/) | 

## Klasifikace tmy (Falchi et al.)

| Hodnota | Kategorie | Popis |
|---------|-----------|-------|
| ≤0.01 | Černá | Přirozená tma |
| 0.01-0.02 | Tmavě šedá | Velmi tmavá |
| 0.02-0.04 | Šedá | Téměř přirozená |
| 0.04-0.08 | Tmavě modrá | Slabé znečištění |
| 0.08-0.16 | Modrá | Mírné znečištění |
| >0.16 | Světle modrá+ | Střední až silné znečištění |

**Doporučený prah pro pozorování meteorů**: < 0.16

## Struktura repozitáře

```
perseidy/
├── data/
│   └── cesko_tma.tif          # Oříznutý Falchi rastr pro ČR (~1 MB)
├── isochrones/
│   ├── isochrone_Praha.geojson
│   ├── isochrone_Brno.geojson
│   └── ...                      # Isochrony pro všech 14 krajů + bonusové lokality
├── output/
│   ├── viewpoints_with_darkness.csv    # Všechna výhledová místa s hodnotou tmy
│   ├── best_sites_per_city.csv         # Nejtemnější místo per kraj
│   ├── reachable_dark_sites.csv        # Průnik: tmavá místa + dojezd < 1h
│   ├── perseidy_regional.html          # Mapa: výběr kraje + izochrona
│   └── perseidy_full_cz.html           # Mapa: celá ČR manuální hledání
├── vyhlidkova_mista_cr.csv     # Zdrojová data výhledových míst (od Michala, kontaminovaná)
├── vyhlidkova_mista_cr_clean.csv       # Vyčištěná data (pouze skutečné vyhlídky)
├── vyhlidkova_mista_cr_astronomystrict.csv       # Přísná varianta pro pozorování oblohy
├── krajska_mista.csv           # Krajská města pro izochrony
├── clean_viewpoints.py         # Čištění vstupních dat (odstraní surveillance kamery atd.)
├── clean_viewpoints_astronomy_strict.py # Přísnější filtrování pro astronomy
├── generate_isochrones.py      # Generování izochron přes ORS API
├── analyze_dark_sites.py       # Hlavní analýza a průniky
├── create_html_maps.py         # Generování HTML map
├── pyproject.toml              # Python dependencies (uv)
└── README.md
```

## Rychlý start

Pokud jsou k dispozici všechna vstupní data, spustit:

```bash
uv run python create_html_maps.py
```

Tím se vygenerují obě hlavní HTML mapy v `output/`.

### Postup krok za krokem

### 1. (Volitelné) Oříznutí GeoTIFF pro ČR

Ořez Česka `data/cesko_tma.tif` z celosvětového GEOTIFFUz původního Falchi rastru:

```bash
uv run python crop_falchi_to_cz.py
```

Výsledek: `data/cesko_tma.tif` (~1 MB). **Poznámka:** Skript potřebuje vstupní `World_Atlas_2015.tif` který není v repozitáři — stáhnout samostatně ze [10.5880/GFZ.1.4.2016.001](https://doi.org/10.5880/GFZ.1.4.2016.001).

### 2. Vyčistit vstupní data (astronomy strict varianta)

Aktivní pipeline používá **astronomy strict** dataset — přísnější filtrování které odstraní rozhledny a věže (nevhodné pro pozorování oblohy kvůli světlu uvnitř objektu):

```bash
uv run python clean_viewpoints_astronomy_strict.py
```

Výstup:
- `vyhlidkova_mista_cr_astronomystrict.csv` — 993 bodů (proti 5395 v clean variantě)
- `output/astronomystrict_filter_report.csv` — detailní report co a proč vypadlo

### 3. Generování izochron

```bash
uv run python generate_isochrones.py
```

Tento krok volá OpenRouteService API 14× (jednou pro každé krajské město).  
**Poznámka**: Free tier má denní limit. Pokud narazíš na limit, buď počkej 24h, nebo použij API key s vyšším limitem.

### 4. Analýza a průniky

```bash
uv run python analyze_dark_sites.py \
    --viewpoints-csv vyhlidkova_mista_cr_astronomystrict.csv \
    --output-suffix _astronomystrict
```

Výstup:
- `output/viewpoints_with_darkness_astronomystrict.csv`
- `output/reachable_dark_sites_astronomystrict.csv`
- `output/best_sites_per_city_astronomystrict.csv`

### 5. Vytvoření HTML map

```bash
uv run python create_html_maps.py
```

Výstup:
- `output/perseidy_regional.html`
- `output/perseidy_full_cz.html`

## Výstupy

| Soubor | Použití |
|--------|---------|
| `best_sites_per_city.csv` | Statická tabulka: top místo pro každý kraj |
| `perseidy_regional.html` | Interaktivní mapa: uživatel vybere kraj, vidí izochronu a tmavá místa |
| `perseidy_full_cz.html` | Interaktivní mapa: prozkoumat celou ČR a najít vlastní místo |

## Citace dat

Pokud používáš tato data ve veřejném projektu:

```
Data světelného znečištění: Falchi, F., Cinzano, P., Duriscoe, D., et al. (2016).
The New World Atlas of Artificial Night Sky Brightness. GFZ Data Services.
https://doi.org/10.5880/GFZ.1.4.2016.001

Original scientific article: Falchi, F., et al. (2016).
The new world atlas of artificial night sky brightness.
Science Advances, 2(6), e1600377.
https://doi.org/10.1126/sciadv.1600377

Data výhledových míst: Michal Kašpárek / Český rozhlas
https://github.com/DataRozhlas/divnovylety
```

## Autoři

- Jaromír Gumulec (analýza, skripty)
- Michal Kašpárek (data výhledových míst)

---

## Budoucí inspirace

### Oblačnost

Idee jak v budoucnu přidat vrstvu oblačnosti:

| Přístup | Problém |
|---------|---------|
| **Open-Meteo API** (direct) | 5395 bodů × API call = rate limit po ~600 requestech |
| **YR.no WMS** | Server neodpovídá / blokuje přístup |
| **CHMI Aladin WMS** | Veřejný endpoint nedostupný |
| **NASA GIBS WMS** | Blokováno CORS / vyžaduje autentizaci |
| **Meteoblue WMS** | Nereaguje na GetCapabilities |

**Možná řešení:**
- Self-hostovaný backend (Node.js/Python) který cachejuje weather data každých 30 minut
- Použití statických forecast obrázků (např. stáhnout PNG z YR.no každý den)
- Integrace s CHMI pokud poskytnou veřejný endpoint

---

## Changelog - Čištění dat vyhlídkových míst (2025-08-02)

### Problém
Původní dataset `vyhlidkova_mista_cr.csv` (17 521 záznamů) byl silně kontaminovaný nesmyslnými záznamy z OSM:

| Typ kontaminace | Počet | Příklad |
|-----------------|-------|---------|
| Surveillance kamery | 11 757 | Městské bezpečnostní kamery |
| Webkamery | 20 | Online webkamery |
| Dopravní značení | 49 | Rychlostní kamery, semafory |
| Jiné nesmysly | ~300 | Budovy bez výhledu, strážnice |

### Řešení
Vytvořen skript `clean_viewpoints.py` s následujícími filtry:

**Zachováno** (skutečná vyhlídková místa):
- `tourism=viewpoint` — vyhlídková místa
- `man_made=observation_tower`, `tower`, `windmill` — rozhledny, větrné mlýny s vyhlídkou
- `tower:type=observation/watchtower/lookout` — věže s výhledem

**Odstraněno**:
- `man_made=surveillance` — všechny typy kamer
- `surveillance=camera/webcam/traffic/average_speed/red_light` — specifické typy monitoringu

### Výsledek
| Soubor | Počet | Popis |
|--------|-------|-------|
| `vyhlidkova_mista_cr_clean.csv` | 5 395 | Všechna vyhlídková místa |
| `vyhlidkova_mista_cr_clean_named.csv` | 1 438 | Pouze pojmenovaná místa |

**Odebráno**: 12 126 neplatných záznamů (69 % původního datasetu)

### Poznámka k kvalitě dat
Vyčištěná data stále mohou obsahovat některé problematické záznamy které nelze automaticky filtrovat:

1. **Nízké objekty (3–5 m)** — 5 bodů s výškou pod 5m může být malé vyhlídkové plošiny nebo chybně tagované body
2. **"Vrcholy hor" v lese** — Některá místa tagovaná jako `tourism=viewpoint` mohou být v lese bez skutečného výhledu (např. "Branžovský les")
3. **Unnamed POI** — 3 957 bodů bez názvu (zůstaly zachovány, mohou být validní vyhlídky)

Tyto body jsou tagované v OSM jako viewpoint což předpokládá výhled, ale manuální ověření každé lokality není možné. Data jsou tedy **doporučena s poznámkou** že některé lokality mohou vyžadovat ověření.

### Poznámka k filtraci astronomy strict

Přísná varianta (`clean_viewpoints_astronomy_strict.py`) dále redukuje data oproti clean variantě:

| Měření | Hodnota |
|--------|---------|
| clean reference | 5395 bodů |
| astronomy strict | 993 bodů |
| vypadlo proti clean | 4402 bodů (81.59 %) |
| Pořád dost | cca 5 bodů v izochroně Praha |

**Proč vyřadit rozhledny?** Rozhledny a věže mají světla uvnitř objektu pro noční návštěvníky, což je dělá nevhodnými pro pozorování oblohy navzdory jejich nadmořské výšce.
