
import html
import re
import os
import psycopg2

from dotenv import load_dotenv
from bs4 import BeautifulSoup
import spacy
import pycountry
import country_converter as coco


# 1. DATABASE CONNECTION

def connect_to_database():
    """
    Connect to PostgreSQL using credentials stored in .env.
    """

    load_dotenv(".env")

    connection = psycopg2.connect(
        host="localhost",
        port=5432,
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

    return connection



# 2. FETCH ARTICLES


def fetch_articles(connection):
    """
    Retrieve articles from the PostgreSQL landing table.
    """

    cursor = connection.cursor()

    cursor.execute("""
        SELECT _dlt_id, title, summary
        FROM dlt_landing.news_articles
        ORDER BY _dlt_id;
    """)

    articles = cursor.fetchall()

    cursor.close()

    return articles



# 3. SAVE EXTRACTED LOCATIONS

def save_article_locations(connection, article_id, locations):
    """
    Save extracted locations for one article in the analytics table.
    """

    cursor = connection.cursor()

    cursor.executemany("""
        INSERT INTO analytics.article_locations (
            article_dlt_id,
            location_name,
            location_type,
            iso2,
            iso3,
            continent,
            subtype
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (article_dlt_id, location_name, location_type)
        DO UPDATE SET
            iso2 = EXCLUDED.iso2,
            iso3 = EXCLUDED.iso3,
            continent = EXCLUDED.continent,
            subtype = EXCLUDED.subtype;
    """, [
        (
            article_id,
            location["name"],
            location["type"],
            location.get("iso2"),
            location.get("iso3"),
            location.get("continent"),
            location.get("subtype")
        )
        for location in locations
    ])

    cursor.close()



# 4. PROCESS ALL ARTICLES


def process_all_articles(connection, nlp, cc):
    """
    Extract and save locations for all articles in PostgreSQL.
    """

    articles = fetch_articles(connection)

    processed_articles = 0
    articles_with_locations = 0
    total_locations = 0

    try:

        # Remove previously extracted locations before rebuilding.
        cursor = connection.cursor()
        cursor.execute("DELETE FROM analytics.article_locations;")
        cursor.close()

        for article_id, title, summary in articles:

            text = prepare_nlp_text(title, summary)

            locations = extract_all_locations(text, nlp, cc)

            save_article_locations(
                connection,
                article_id,
                locations
            )

            processed_articles += 1

            if locations:
                articles_with_locations += 1
                total_locations += len(locations)

            if processed_articles % 50 == 0:
                print(
                    f"Processed {processed_articles}/{len(articles)} articles"
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    print("\nProcessing complete!")
    print("Articles processed:", processed_articles)
    print("Articles with locations:", articles_with_locations)
    print("Total locations extracted:", total_locations)

    return processed_articles, articles_with_locations, total_locations



# 5. CLEAN HTML AND PREPARE NLP TEXT


def clean_html(text):
    """
    Remove HTML tags and decode HTML entities from article text.
    """

    if not text:
        return ""

    text = html.unescape(text)

    soup = BeautifulSoup(text, "html.parser")

    cleaned_text = soup.get_text(" ", strip=True)

    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    return cleaned_text


def prepare_nlp_text(title, summary):
    """
    Combine the cleaned article title and summary for NLP processing.
    """

    cleaned_title = clean_html(title)
    cleaned_summary = clean_html(summary)

    combined_text = f"{cleaned_title} {cleaned_summary}"

    return re.sub(r"\s+", " ", combined_text).strip()



# 6. EXTRACT COUNTRIES AND TERRITORIES


def extract_countries(text, nlp, cc):
    """
    Extract countries and ISO-recognised territories from article text.
    Standardise their names, ISO codes and continent information.
    """

    country_display_names = {
        "Iran, Islamic Republic of": "Iran",
        "Venezuela, Bolivarian Republic of": "Venezuela",
    }

    doc = nlp(text)

    countries = []
    seen_countries = set()

    for ent in doc.ents:

        # Only examine entities spaCy identifies as geopolitical locations.
        if ent.label_ != "GPE":
            continue

        try:
            country = pycountry.countries.lookup(ent.text)

        except LookupError:
            # Ignore cities, states and other GPEs not found in pycountry.
            continue

        # Avoid storing the same country more than once per article.
        if country.alpha_3 in seen_countries:
            continue

        continent = cc.convert(
            country.alpha_3,
            to="Continent_7"
        )

        countries.append({
            "country": country_display_names.get(
                country.name,
                country.name
            ),
            "iso2": country.alpha_2,
            "iso3": country.alpha_3,
            "continent": continent
        })

        seen_countries.add(country.alpha_3)

    return countries



# 7. EXTRACT CONTINENTS


def extract_continents(text):
    """
    Identify the seven continents mentioned in article text.
    """

    continents = [
        "Africa",
        "Antarctica",
        "Asia",
        "Europe",
        "North America",
        "South America",
        "Oceania"
    ]

    extracted_continents = []

    for continent in continents:

        pattern = rf"\b{re.escape(continent)}\b"

        if re.search(pattern, text, re.IGNORECASE):

            extracted_continents.append({
                "name": continent,
                "type": "continent"
            })

    return extracted_continents



# 8. EXTRACT GEOGRAPHIC REGIONS


def extract_geographic_regions(text):
    """
    Identify selected broad geographic regions using custom rules.
    """

    known_regions = {

        # Global regions
        "Latin America": r"\bLatin America\b",
        "Caribbean": r"\bCaribbean\b",
        "Middle East": r"\bMiddle East\b",
        "Global South": r"\bGlobal South\b",

        # Asia
        "South Asia": r"\bSouth Asia\b",
        "Southeast Asia": r"\bSoutheast Asia\b",
        "East Asia": r"\bEast Asia\b",
        "Central Asia": r"\bCentral Asia\b",
        "West Asia": r"\bWest Asia\b",

        # Europe
        "Northern Europe": r"\bNorthern Europe\b",
        "Southern Europe": r"\bSouthern Europe\b",
        "Eastern Europe": r"\bEastern Europe\b",
        "Western Europe": r"\bWestern Europe\b",
        "Central Europe": r"\bCentral Europe\b",

        # Africa
        "North Africa": r"\bNorth Africa\b",
        "West Africa": r"\bWest Africa\b",
        "East Africa": r"\bEast Africa\b",
        "Central Africa": r"\bCentral Africa\b",
        "Southern Africa": r"\bSouthern Africa\b",
        "Sub-Saharan Africa": r"\bSub-Saharan Africa\b",
        "Sahel": r"\bSahel\b",
        "Horn of Africa": r"\bHorn of Africa\b",
        "Great Lakes Region": r"\bGreat Lakes Region\b",
        "Congo Basin": r"\bCongo Basin\b",

        # Americas
        "Central America": r"\bCentral America\b",
        "Amazon Basin": r"\bAmazon Basin\b",

        # Oceania
        "Pacific Islands": r"\bPacific Islands\b",

        # Polar region
        "Arctic": r"\bArctic\b(?!\s+Ocean)"
    }

    geographic_regions = []

    for name, pattern in known_regions.items():

        if re.search(pattern, text, re.IGNORECASE):

            geographic_regions.append({
                "name": name,
                "type": "geographic_region"
            })

    return geographic_regions



# 9. EXTRACT WATER BODIES


def extract_water_bodies(text):
    """
    Identify selected oceans and other major bodies of water.
    """

    known_water_bodies = {
        "Atlantic Ocean": r"\b(?:Atlantic Ocean|Atlantic)\b",
        "Pacific Ocean": r"\bPacific Ocean\b",
        "Indian Ocean": r"\bIndian Ocean\b",
        "Arctic Ocean": r"\bArctic Ocean\b",
        "Southern Ocean": r"\bSouthern Ocean\b",
        "Mediterranean Sea": r"\bMediterranean Sea\b",
        "North Sea": r"\bNorth Sea\b",
        "Baltic Sea": r"\bBaltic Sea\b"
    }

    water_bodies = []

    for name, pattern in known_water_bodies.items():

        if re.search(pattern, text, re.IGNORECASE):

            water_bodies.append({
                "name": name,
                "type": "water_body"
            })

    return water_bodies



# 10. COMBINE ALL GEOGRAPHIC EXTRACTION FUNCTIONS


def extract_all_locations(text, nlp, cc):
    """
    Extract countries, continents, geographic regions,
    and water bodies from article text.
    """

    locations = []

    # Countries and territories
    for country in extract_countries(text, nlp, cc):

        locations.append({
            "name": country["country"],
            "type": "country",
            "iso2": country["iso2"],
            "iso3": country["iso3"],
            "continent": country["continent"]
        })

    # Continents
    locations.extend(extract_continents(text))

    # Geographic regions
    locations.extend(extract_geographic_regions(text))

    # Oceans and seas
    locations.extend(extract_water_bodies(text))

    return locations

