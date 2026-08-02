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
- **Zdroj**: OpenStreetMap přes Overpass API
- **Kategorie**: `tourism=viewpoint`, `man_made=observation_tower`, `natural=peak`
- **Ošetření**: Filtrování surveillance kamer a nesprávných tagů

### Izochrony
- **Zdroj**: OpenRouteService API
- **Profil**: Driving-car
- **Časový interval**: 1 hodina od každého krajského města

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
│   └── cesko_tma.tif          # Oříznutý Falchi rastr pro ČR (~50-100 MB)
├── isochrones/
│   ├── isochrone_Praha.geojson
│   ├── isochrone_Brno.geojson
│   └── ...                      # Isochrony pro všech 14 krajů
├── output/
│   ├── viewpoints_with_darkness.csv    # Všechna výhledová místa s hodnotou tmy
│   ├── dark_sites.csv                  # Filtr: místa s tma < 0.16
│   ├── reachable_dark_sites.csv        # Průnik: tmavá místa + dojezd < 1h
│   ├── best_sites_per_city.csv         # Nejtemnější místo per kraj
│   ├── dark_sites_map.html             # Interaktivní mapa
│   └── all_isochrones_map.html         # Mapa s izochronami
├── vyhlidkova_mista_cr.csv     # Zdrojová data výhledových míst
├── krajska_mista.csv           # Krajská města pro izochrony
├── crop_falchi_to_cz.py        # Skript pro oříznutí GeoTIFF
├── generate_isochrones.py      # Generování izochron přes ORS API
├── analyze_dark_sites.py       # Hlavní analýza a průniky
├── requirements.txt            # Python dependencies
└── README.md
```

## Instalace

```bash
# Vytvořit virtuální prostředí
python -m venv .venv
source .venv/bin/activate  # nebo Windows: .venv\Scripts\activate

# Nainstalovat závislosti
pip install -r requirements.txt

# Přidat API klíč do config.py (viz níže)
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

Máš dvě možnosti:

**A) V QGISu** (doporučeno pro rychlost):
1. Načti `World_Atlas_2015.tif` do QGIS
2. Vektor → Geoprocessing → Clip Raster by Mask Layer
3. Jako masku zvol `prac_obrys_cesko.geojson`
4. Výsledek ulož jako `data/cesko_tma.tif`

**B) Python skriptem** (reprodukovatelnost):
```bash
python crop_falchi_to_cz.py
```

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
- HTML interaktivní mapa

## Výstupy

Po dokončení analýzy najdeš v `output/`:

| Soubor | Obsah |
|--------|-------|
| `best_sites_per_city.csv` | Nejtemnější dostupné místo pro každé krajské město |
| `dark_sites_map.html` | Interaktivní mapa se všemi tmavými body |
| `reachable_dark_sites.csv` | Všechna tmavá místa do 1h dojezdu |

## Použití v článku

Pro datové novináře:

1. **Statická tabulka**: `best_sites_per_city.csv` obsahuje top místo pro každý kraj
2. **Interaktivní komponenta**: `dark_sites_map.html` lze embednout nebo zveřejnit na GitHub Pages
3. **Izochrony**: `all_isochrones_map.html` ukazuje dosah z větších měst

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
```

## Autoři

- Jaromír Gumulec (analýza, skripty)
- Michal Kašpárek (data výhledových míst, UX)
- Petr Kočí (produkce, článkek)
