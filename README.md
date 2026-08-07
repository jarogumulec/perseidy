# Perseidy - Nejtemnější místa pro pozorování meteorů

Projekt hledá optimální místa v České republice pro pozorování Perseid a dalších meteorických rojů na základě:
- **Světelného znečištění** (Falchi et al. 2016 atlas)
- **Výhledových míst** z OSM (rozhledny, vyhlídky, vrcholy)
- **Dostupnosti** (izochrony dojezdu z krajských měst)

## Proč právě Falchi atlas? (i když data jsou z roku 2015)

Při výběru datasetu pro světelné znečištění jsme narazili na modernější alternativy jako VIIRS Black Marble nebo WorldPop. Zásadní rozdíl:

| Dataset | Co měří | Vhodné pro astronomy? |
|---------|---------|----------------------|
| **Falchi 2015** | Jas noční oblohy (skyglow) po atmosférickém rozptylu | ✅ ANO - přímo to, co vidíš nad hlavou |
| **VIIRS / Black Marble** | Světlo vycházející ze země směrem vzhůru | ❌ NE - ukazuje města/ulice, ne kvalitu oblohy |

Pro astronomii není podstatné kolik světla vychází ze zemského povrchu, ale jak světlá je obloha nad tebou. Mezi těmito dvěma veličinami leží atmosférický rozptyl - a právě ten Falchi modeluje.

**Závěr:** I když jsou Falchi data z roku 2015, stále poskytují smysluplnější informaci pro výběr pozorovacích lokalit než aktuálnější VIIRS rastry. Relativní pořadí tmavých oblastí v ČR se za posledních 10 let významně nezměnilo.

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
- **Kategorie**: `tourism=viewpoint`, `man_made=observation_tower`, `natural=peak`
- **Čištění**: Původní data jsou kontaminovaná surveillance kamerami, webkamerami a dopravním značením. Skript `clean_viewpoints.py` vyfiltruje pouze skutečná vyhlídková místa (5395 z 17521 záznamů).

### Izochrony
- **Zdroj**: OpenRouteService API
- **Profil**: Driving-car
- **Časový interval**: 1 hodina od každého krajského města

## Interaktivní mapy

Po spuštění `create_html_maps.py` najdeš v `output/` tři varianty map:

| Soubor | Popis |
|--------|-------|
| `perseidy_regional.html` | Mapa ČR s vrstvami - zaškrtávací menu vlevo, legenda vpravo dole |
| `perseidy_full_cz.html` | Celá ČR s výhledovými místy - "najdi si svoje místo" |
| `perseidy_top_sites.html` | Nejtemnější místa per kraj s přehledovou tabulkou |

**Vlastnosti všech map:**
- **Dark/Light toggle**: Tlačítko vpravo nahoře pro přepnutí světlé/tmavé podkladové mapy
- **Layer control**: Zaškrtávací seznam vrstev (Světelné znečištění, Izochrony, Rozhledová místa)
- **Legenda**: Kompaktní barevná škála Falchi vpravo dole

Pro GitHub Pages je připravený vstupní web v `docs/index.html`. Když nastavíš Pages na větev `main` a složku `docs`, bude hlavní adresa `https://jarogumulec.github.io/perseidy/` a HTML soubory budou canonical v `docs/output/`. Původní přímé odkazy do `output/` zůstanou funkční, protože generované HTML se zrcadlí i do kořenového `output/` jako legacy mirror.

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
│   └── ...                      # Isochrony pro všech 14 krajů
├── output/
│   ├── viewpoints_with_darkness.csv    # Všechna výhledová místa s hodnotou tmy
│   ├── best_sites_per_city.csv         # Nejtemnější místo per kraj
│   ├── reachable_dark_sites.csv        # Průnik: tmavá místa + dojezd < 1h
│   ├── perseidy_regional.html          # Mapa: výběr kraje + izochrona
│   ├── perseidy_full_cz.html           # Mapa: celá ČR manuální hledání
│   └── perseidy_top_sites.html         # Mapa: top místa per kraj
├── vyhlidkova_mista_cr.csv     # Zdrojová data výhledových míst (od Michala, kontaminovaná)
├── vyhlidkova_mista_cr_clean.csv       # Vyčištěná data (pouze skutečné vyhlídky)
├── vyhlidkova_mista_cr_clean_named.csv # Pouze pojmenovaná místa (bez "Unnamed POI")
├── vyhlidkova_mista_cr_astronomystrict.csv       # Přísná varianta pro pozorování oblohy
├── vyhlidkova_mista_cr_astronomystrict_named.csv # Přísná varianta, jen pojmenované body
├── krajska_mista.csv           # Krajská města pro izochrony
├── crop_falchi_to_cz.py        # Skript pro oříznutí GeoTIFF
├── clean_viewpoints.py         # Čištění vstupních dat (odstraní surveillance kamery atd.)
├── clean_viewpoints_astronomy_strict.py # Přísnější filtrování pro astronomy
├── generate_isochrones.py      # Generování izochron přes ORS API
├── analyze_dark_sites.py       # Hlavní analýza a průniky
├── create_html_maps.py         # Generování HTML map
├── pyproject.toml              # Python dependencies (uv)
├── uv.lock                     # Zamcene verze zavislosti (uv)
└── README.md
```

## Instalace

```bash
# Synchronizace prostředí podle pyproject.toml/uv.lock
uv sync

# (Volitelné) aktivace prostředí
source .venv/bin/activate

# Přidání nové závislosti
uv add nazev-balicku
```

## Konfigurace

Vytvoř `config.py` ve stejném adresáři jako 
skripty:

```python
# OpenRouteService API key
ORS_API_KEY = "tvuj-api-klic-zde"
```

API klíč získáš na: https://openrouteservice.org/dev/#/signup

## Postup

### 1. Oříznutí GeoTIFF pro ČR

**Python skriptem:**
```bash
uv run python crop_falchi_to_cz.py
```

Výsledek: `data/cesko_tma.tif` (~1 MB)

### 2. (Volitelné) Vyčistit vstupní data

Pokud chceš použít čerstvá vyčištěná data:

```bash
uv run python clean_viewpoints.py
```

Výstup:
- `vyhlidkova_mista_cr_clean.csv` - Všechna vyhlídková místa (5395 záznamů)
- `vyhlidkova_mista_cr_clean_named.csv` - Pouze pojmenovaná místa (1438 záznamů)

**Poznámka**: Analýza automaticky používá vyčištěná data (`vyhlidkova_mista_cr_clean.csv`).

### 2b. Astronomy strict varianta (oddělená větev, nic nepřepisuje)

Pokud chceš přísnější dataset pro pozorování oblohy (bez rozhleden/věží a bez části problematických názvů), spusť:

```bash
uv run python clean_viewpoints_astronomy_strict.py
```

Výstup:
- `vyhlidkova_mista_cr_astronomystrict.csv`
- `vyhlidkova_mista_cr_astronomystrict_named.csv`
- `output/astronomystrict_filter_report.csv` (srovnání počtů a důvody vyřazení)

Naměřený dopad (aktuální data):
- clean reference: `5395` bodů
- astronomy strict: `993` bodů
- vypadlo proti clean: `4402` bodů (`81.59 %`)
- Pořád dost - cca 5 - v izochroně Praha

### 3. Generování izochron

```bash
uv run python generate_isochrones.py
```

Tento krok volá OpenRouteService API 14× (jednou pro každé krajské město).  
**Poznámka**: Free tier má denní limit. Pokud narazíš na limit, buď počkej 24h, nebo použij API key s vyšším limitem.

### 3. Analýza a průniky

```bash
uv run python analyze_dark_sites.py
```

Výstup:
- CSV s nejlepšími místy per kraj
- CSV se všemi body a jejich hodnotou tmy

Pro astronomy strict variantu (oddělené výstupy se suffixem):

```bash
uv run python analyze_dark_sites.py \
	--viewpoints-csv vyhlidkova_mista_cr_astronomystrict.csv \
	--output-suffix _astronomystrict
```

Vygeneruje například:
- `output/viewpoints_with_darkness_astronomystrict.csv`
- `output/reachable_dark_sites_astronomystrict.csv`
- `output/best_sites_per_city_astronomystrict.csv`

### 4. Vytvoření HTML map

```bash
uv run python create_html_maps.py
```

Výstup: 2 HTML mapy v `output/`

`create_html_maps.py` je nyní nastavený natvrdo na astronomy strict vstupy
(`output/*_astronomystrict.csv`), ale HTML ukládá pod standardní názvy:

- `output/perseidy_regional.html`
- `output/perseidy_full_cz.html`

Spuštění:

```bash
uv run python create_html_maps.py
```

Tímto se původní HTML mapy přepisují astronomy strict obsahem.

CSV varianty zůstávají odděleně zachované:
- clean: `vyhlidkova_mista_cr_clean.csv`, `vyhlidkova_mista_cr_clean_named.csv`
- astronomy strict: `vyhlidkova_mista_cr_astronomystrict.csv`, `vyhlidkova_mista_cr_astronomystrict_named.csv`

Pro rychlý návrat na původní clean variantu stačí v `create_html_maps.py`
odkomentovat původní trojici vstupních cest a zakomentovat astronomy strict trojici.

## Výstupy pro článek

| Soubor | Použití |
|--------|---------|
| `best_sites_per_city.csv` | Statická tabulka: top místo pro každý kraj |
| `perseidy_regional.html` | Interaktivní mapa: uživatel vybere kraj, vidí izochronu a tmavá místa |
| `perseidy_full_cz.html` | Interaktivní mapa: prozkoumat celou ČR a najít vlastní místo |
| `perseidy_top_sites.html` | Přehled nejtemnějších míst s hvězdičkami |

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

## TODO / Known Issues

### ❌ Mapa s oblačností (nefunkční)

Pokus o vytvoření interaktivní mapy s aktuální oblačností **selhal**. Problémy:

| Přístup | Problém |
|---------|---------|
| **Open-Meteo API** (direct) | 5395 bodů × API call = rate limit po ~600 requestech |
| **YR.no WMS** | Server neodpovídá / blokuje přístup |
| **CHMI Aladin WMS** | Veřejný endpoint nedostupný |
| **NASA GIBS WMS** | Blokováno CORS / vyžaduje autentizaci |
| **Meteoblue WMS** | Nereaguje na GetCapabilities |

**Důvod selhání:** Pro zveřejnění veřejné webové stránky potřebujeme buď:
1. **Placené API** (OpenWeatherMap, Windy.com) — tokeny by byly rychle vyčerpány
2. **Veřejný WMS server** — žádný z evropských meteorologických ústavů nemá otevřený bezplatný WMS pro ČR/Evropu
3. **Self-hosted backend** — stahovat a cacheovat předpovědi na vlastním serveru

**Možná řešení (budoucnost):**
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

### Budoucí vylepšení
- Přidat filtr na minimální výšku (`height > 5m`) pro rozhledny
- Ruční kontrola a odstranění známých chybných lokalit
- Integrace s dalšími datovými zdroji (např. oficiální seznam rozhleden AČK)
