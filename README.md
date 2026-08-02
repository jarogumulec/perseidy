# Perseidy - Nejtemnější místa pro pozorování meteorů

Projekt hledá optimální místa v České republice pro pozorování Perseid a dalších meteorických rojů na základě:
- **Světelného znečištění** (Falchi et al. 2016 atlas)
- **Výhledových míst** z OSM (rozhledny, vyhlídky, vrcholy)
- **Dostupnosti** (izochrony dojezdu z krajských měst)

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

### Izochrony
- **Zdroj**: OpenRouteService API
- **Profil**: Driving-car
- **Časový interval**: 1 hodina od každého krajského města

## Interaktivní mapy

Po spuštění `create_html_maps.py` najdeš v `output/` tři varianty map:

| Soubor | Popis |
|--------|-------|
| `perseidy_regional.html` | Výběr kraje + izochrona + tmavá místa v dosahu |
| `perseidy_full_cz.html` | Celá ČR s výhledovými místy - "najdi si svoje místo" |
| `perseidy_top_sites.html` | Nejtemnější místa per kraj s hvězdičkami |

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
├── vyhlidkova_mista_cr.csv     # Zdrojová data výhledových míst (od Michala)
├── krajska_mista.csv           # Krajská města pro izochrony
├── crop_falchi_to_cz.py        # Skript pro oříznutí GeoTIFF
├── generate_isochrones.py      # Generování izochron přes ORS API
├── analyze_dark_sites.py       # Hlavní analýza a průniky
├── create_html_maps.py         # Generování HTML map
├── requirements.txt            # Python dependencies
└── README.md
```

## Instalace

```bash
# Vytvořit virtuální prostředí
python3 -m venv .venv
source .venv/bin/activate

# Nainstalovat závislosti
pip install -r requirements.txt
```

## Konfigurace

Vytvoř `config.py` ve stejném adresáři jako skripty:

```python
# OpenRouteService API key
ORS_API_KEY = "tvuj-api-klic-zde"
```

API klíč získáš na: https://openrouteservice.org/dev/#/signup

## Postup

### 1. Oříznutí GeoTIFF pro ČR

**Python skriptem:**
```bash
python crop_falchi_to_cz.py
```

Výsledek: `data/cesko_tma.tif` (~1 MB)

### 2. Generování izochron

```bash
python generate_isochrones.py
```

Tento krok volá OpenRouteService API 14× (jednou pro každé krajské město).  
**Poznámka**: Free tier má denní limit. Pokud narazíš na limit, buď počkej 24h, nebo použij API key s vyšším limitem.

### 3. Analýza a průniky

```bash
python analyze_dark_sites.py
```

Výstup:
- CSV s nejlepšími místy per kraj
- CSV se všemi body a jejich hodnotou tmy

### 4. Vytvoření HTML map

```bash
python create_html_maps.py
```

Výstup: 3 HTML mapy v `output/`

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
- Michal Kašpárek (data výhledových míst, UX)
- Petr Kočí (produkce, článek)
