# GitHub Issues pro Perseidy projekt

## Issue 1: Upozornění na stáří Falchi dat

**Title:** Poznámka: Falchi data jsou z roku 2015

**Body:**
```
## Upozornění na stáří dat

**Světelné znečištění (Falchi et al. 2015)** - data mají více než 10 let.

### Potenciální problémy:
- Mnoha místy se světelné znečištění zvýšilo od roku 2015
- Některá 'tmavá' místa mohou být dnes již světlejší
- Pro přesné plánování doporučujeme ruční kontrolu via Mapy.cz nebo Google Maps

### Doporučení:
- Vždy ověřit aktuální stav před návštěvou
- Hledat recenze a fotky z posledních 2-3 let
```

---

## Issue 2: Filtrování Michalových dat z OSM

**Title:** Filtrování divných výhledových míst (hasičárny, surveillance)

**Body:**
```
## Problém s kvalitou dat z OSM

Michalova extrakce výhledových míst obsahuje některá nevhodná místa:
- Hasičárny s "výhledem" ve střed obce
- Surveillance kamery místo skutečných vyhlídek
- Rozcestníky u rozhleden bez vlastního výhledu
- Body s nesprávnými tagy

### Navrhované řešení:
- [ ] Ruční revize CSV před publikací
- [ ] Doplnit filtr na výšku budov (vyhodit nízké budovy)
- [ ] Přidat kolonii s obrázkovým ověřením (Google Street View API?)
- [ ] Manuální značekování špatných bodů pro budoucí filtrování

### Priorita:
Střední - zatím necháváme všechna místa, uživatel si najde svoje.
```

---

## Issue 3: Okresní izochrony (30 min)

**Title:** Implementovat 30min izochrony pro okresy

**Body:**
```
## Rozšíření o okresní úroveň

### Popis:
Přidat 30min izochrony pro 74 okresů + Praha kromě stávajících 14 krajů.

### Status:
- [x] Příprava CSV s okresními městy (`okresni_mesta.csv`)
- [x] Skript `generate_okres_isochrones.py` připraven
- [ ] Generování izochron (74 API callů × 2s = ~2.5 minut)
- [ ] Výpočet statistik pro každou izochronu
- [ ] Integrace do HTML map

### Poznámky:
- API limit ORS free tier může být problém
- Možná rozdělit generování na více dní nebo použít paid tier
```

---

## Issue 4: Vylepšení UI/UX

**Title:** Vylepšení uživatelského rozhraní

**Body:**
```
## Návrhy na vylepšení

### Regional map:
- [x] Dropdown pro výběr kraje
- [x] Implicitně zobrazen první kraj (Praha)
- [ ] Přidat zoom na vybraný region
- [ ] Ukázat statistiky v popupu při kliknutí na isochronu

### Full CZ map:
- [x] Nejtemnější místo zvýrazněno
- [ ] Filtr podle minimální darkness hodnoty
- [ ] Search box pro hledání konkrétního místa

### Top sites map:
- [x] Tabulka statistik pod mapou
- [ ] Export do PDF/CSV
- [ ] Tlačítko "Nahodit náhodné místo"
```
