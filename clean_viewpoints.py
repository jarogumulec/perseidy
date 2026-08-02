#!/usr/bin/env python3
"""
Čištění vstupních dat vyhlídkových míst z OSM.

Odstraňuje kontaminaci: surveillance kamery, webkamery, dopravní značení,
nízké budovy bez výhledu a jiné nesmysly.

Výstup: čistá tabulka pouze se skutečnými vyhlídkovými místy.
"""

import csv
import pandas as pd

INPUT_FILE = 'vyhlidkova_mista_cr.csv'
OUTPUT_FILE = 'vyhlidkova_mista_cr_clean.csv'

# Kritéria pro zařazení jako vyhlídkové místo
VALID_TOURISM = ['viewpoint']
VALID_MAN_MADE = ['observation_tower', 'windmill', 'tower']  # rozhledny, větrné mlýny s vyhlídkou
VALID_TOWER_TYPE = ['tower', 'observation', 'watchtower', 'lookout']  # rozhledny
VALID_NATURAL = ['peak']  # vrcholy hor

def is_valid_viewpoint(row):
    """
    Zkontroluje zda je záznam skutečným vyhlídkovým místem.

    Odstraní:
    - surveillance kamery (man_made=surveillance)
    - webkamery (surveillance in [camera, webcam])
    - dopravní značení (surveillance in [traffic, average_speed, red_light])
    - budovy bez výhledu (building set and not viewpoint/tower)
    """
    tourism = row.get('tourism', '')
    man_made = row.get('man_made', '')
    tower_type = row.get('tower:type', '')
    natural = row.get('natural', '')
    surveillance = row.get('surveillance', '')
    building = row.get('building', '')

    # OK: tourism=viewpoint
    if tourism in VALID_TOURISM:
        return True

    # OK: man_made=observation_tower nebo windmill
    if man_made in VALID_MAN_MADE:
        return True

    # OK: tower:type=tower (rozhledny)
    if tower_type in VALID_TOWER_TYPE:
        return True

    # OK: natural=peak (vrcholy hor)
    if natural in VALID_NATURAL:
        return True

    # NE: surveillance kamery
    if man_made == 'surveillance':
        return False

    # NE: surveillance typy (camera, webcam, traffic, atd.)
    if surveillance in ['camera', 'webcam', 'traffic', 'average_speed',
                        'red_light', 'checkpoint', 'speed']:
        return False

    # NE: běžné budovy bez výhledu
    if building and building not in ['viewpoint', 'tower']:
        return False

    return False

def round_coordinates(lat, lon, decimals=4):
    """Zaokrouhlí souřadnice na zadaný počet desetinných míst."""
    return round(float(lat), decimals), round(float(lon), decimals)

def main():
    print(f"Načítám data z {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Naloženo {len(df)} záznamů")

    # Zobrazit statistiky před filtrováním
    print("\n=== Před filtrováním ===")
    print(f"tourism=viewpoint: {len(df[df['tourism'] == 'viewpoint'])}")
    print(f"man_made=observation_tower: {len(df[df['man_made'] == 'observation_tower'])}")
    print(f"man_made=surveillance (kamery): {len(df[df['man_made'] == 'surveillance'])}")
    print(f"tower:type=tower: {len(df[df['tower:type'] == 'tower'])}")

    # Filtruje pouze validní vyhlídková místa
    valid_rows = []
    for idx, row in df.iterrows():
        if is_valid_viewpoint(row):
            valid_rows.append(row)

    df_clean = pd.DataFrame(valid_rows)
    print(f"\n=== Po filtrování ===")
    print(f"Zůstalo {len(df_clean)} vyhlídkových míst")
    print(f"Odebráno {len(df) - len(df_clean)} neplatných záznamů")

    # Zjednoduší na name, lat, lon s zaokrouhlenými souřadnicemi
    df_output = pd.DataFrame()
    df_output['name'] = df_clean['name']

    # Zaokrouhlí souřadnice
    df_output['lat'] = df_clean.apply(
        lambda r: round_coordinates(r['lat'], r['lon'])[0], axis=1
    )
    df_output['lon'] = df_clean.apply(
        lambda r: round_coordinates(r['lat'], r['lon'])[1], axis=1
    )

    # Odstraní řádky kde je název "Unnamed POI" a nemají jiný identifikátor
    # Zachová pokud mají nějaký smysluplný název
    print(f"\nZáznamů s 'Unnamed POI': {len(df_output[df_output['name'] == 'Unnamed POI'])}")

    # Uloží výstup
    df_output.to_csv(OUTPUT_FILE, index=False)
    print(f"\nUloženo do {OUTPUT_FILE}")

    # Zobrazí ukázku
    print("\n=== Ukázka prvních 10 záznamů ===")
    print(df_output.head(10).to_string())

    # Statistiky podle typu
    print("\n=== Typy vyhlídek v čistých datech ===")
    df_full = pd.read_csv(INPUT_FILE)
    df_full_clean = df_full[df_full.apply(is_valid_viewpoint, axis=1)]
    print(f"tourism=viewpoint: {len(df_full_clean[df_full_clean['tourism'] == 'viewpoint'])}")
    print(f"man_made=observation_tower: {len(df_full_clean[df_full_clean['man_made'] == 'observation_tower'])}")
    print(f"tower:type=tower: {len(df_full_clean[df_full_clean['tower:type'] == 'tower'])}")
    if 'natural' in df_full_clean.columns:
        print(f"natural=peak: {len(df_full_clean[df_full_clean['natural'] == 'peak'])}")

if __name__ == '__main__':
    main()
