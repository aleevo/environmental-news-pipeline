
from scripts.clean_article_text import clean_article_text



# 1. KEYWORD GROUPS


# Strong indicators: clear environmental or scientific subjects
STRONG_KEYWORDS = [

    # Climate change and atmosphere
    "climate change",
    "global warming",
    "greenhouse gas",
    "climate adaptation",
    "climate resilience",
    "climate protection",
    "climate progress",
    "climate forecasts",
    "climate models",
    "climate finance",
    "climate aid",
    "el nino",
    "atmosphere",

    # Carbon and fossil fuels
    "carbon emissions",
    "carbon dioxide",
    "carbon cycle",
    "fossil fuel emissions",
    "fossil fuel extraction",
    "fossil fuel dependence",
    "fossil fuel supply",
    "fossil fuel transition",
    "oil wells",
    "oil well",
    "oil extraction",
    "oil drilling",

    # Energy and decarbonisation
    "renewable energy",
    "clean energy",
    "clean power",
    "solar energy",
    "solar surge",
    "green hydrogen",
    "green energy transition",
    "ai native grid",

    # Biodiversity, wildlife and ecosystems
    "biodiversity",
    "wildlife",
    "endangered species",
    "critically endangered",
    "species conservation",
    "species extinction",
    "moth species",
    "pollinators",
    "habitat",
    "protected habitat",
    "ecosystem",
    "saola",
    "wildlife conservation",
    "wildlife trafficking",
    "human wildlife coexistence",
    "elephant conflict",

    # Forests, land and soil
    "deforestation",
    "forest conservation",
    "tropical forest",
    "forest protection",
    "greenway",
    "Cities and built environment",
    "urban sustainability",
    "green cities",
    "urban green space",
    "indigenous territory",
    "indigenous land",
    "land rights",

    # Water, wetlands and oceans
    "water pollution",
    "water resilience",
    "water management",
    "water scarcity",
    "water shortages",
    "water resources",
    "water bodies",
    "water status",
    "water challenges",
    "aquifer",
    "wastewater treatment",
    "wastewater",
    "constructed wetlands",
    "wetland",
    "wetland conservation",
    "coral reef",
    "marine pollution",
    "ocean conservation",
    "ocean action",
    "ocean current",
    "ocean currents",
    "ocean for climate solutions",
    "ocean climate solutions",
    "ocean-based climate solutions",
    "atlantic meridional overturning circulation",
    "coastal sea levels",
    "sand mining",
    "sea turtle conservation",
    "turtle conservation",
    "loggerhead turtles",

    # Pollution, plastics and waste
    "air pollution",
    "air quality",
    "microplastic",
    "plastic pollution",
    "plastic packaging",
    "packaging waste",
    "plastic waste exports",
    "electronic waste",
    "e waste",
    "zero pollution",
    "environmental damages",

    # Recycling and circular economy
    "circular economy",
    "battery recycling",
    "recycling targets",
    "resource conservation",
    "resource efficiency",
    "product repairs",
    "bio-based plastic",
    "bioeconomy",

    # Agriculture and food systems
    "sustainable agriculture",
    "livestock emissions",
    "poultry and pig rearing",
    "liquid digestate",
    "chemical fertiliser",
    "chemical fertilizer",

    # Environmental policy and performance
    "environmental protection",
    "environmental legislation",
    "environmental impact",
    "environmental performance",
    "eu ecolabel",

    # Earth science and natural hazards
    "subduction zone",
    "tectonic",
    "earthquake",
    "volcanic activity",

    # Polar regions and cryosphere
    "sea ice",
    "ice melt",
    "arctic warming",
    "ice sheet",
]


# Weak indicators: potentially relevant, but need context
WEAK_KEYWORDS = [

    "storm",
    "storm",
    "hurricane",
    "flood",
    "drought",
    "wildfire",
    "agriculture",
    "water resources",
    "carbon",
    "species",
    "land use",
    "satellite",
    "hurricane",
    "flood",
    "drought",
    "wildfire",
    "agriculture",
    "carbon",
    "species",
    "land use",
    "satellite",
]


# Indicators of subjects generally outside the project's scope
# These provide evidence but do not automatically determine
# the final match status.
UNRELATED_KEYWORDS = [

    "astronomy",
    "exoplanet",
    "galaxy",
    "black hole",
    "saturn",
    "space telescope",
    "astronomy picture of the day",
]


# 2. RULE-BASED CLASSIFICATION


def predict_relevance_rule_based(title, summary):

    """
    Classify an article according to the strength of its
    environmental or scientific keyword matches.

    Possible statuses:
        strong_match
        partial_match
        no_match
    """

    # Clean the article summary
    cleaned_summary = clean_article_text(summary)

    # Combine title and summary
    text = f"{title or ''} {cleaned_summary}".lower()

    # Normalize different types of hyphens
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace("—", " ")
    text = text.replace("\u2011", " ")

    # Normalize ampersands
    text = text.replace("&", " and ")

    # Remove repeated whitespace
    text = " ".join(text.split())

    # Ignore fossil-fuel wording when explicitly used
    # as a contrast rather than the article's subject.
    text_for_matching = text.replace(
        "unlike fossil fuel emissions",
        ""
    )

    # Find matching keywords
    strong_matches = [
        keyword
        for keyword in STRONG_KEYWORDS
        if keyword in text_for_matching
    ]

    weak_matches = [
        keyword
        for keyword in WEAK_KEYWORDS
        if keyword in text_for_matching
    ]

    unrelated_matches = [
        keyword
        for keyword in UNRELATED_KEYWORDS
        if keyword in text_for_matching
    ]

   
    # Determine match strength
   

    if strong_matches:

        status = "strong_match"
        confidence = 0.85

        evidence = (
            "Strong indicators: "
            + ", ".join(strong_matches)
        )

    elif weak_matches:

        status = "partial_match"
        confidence = 0.60

        evidence = (
            "Partial indicators: "
            + ", ".join(weak_matches)
        )

    else:

        status = "no_match"
        confidence = 0.50

        if unrelated_matches:

            evidence = (
                "No recognised environmental/scientific "
                "indicators. Other subject indicators: "
                + ", ".join(unrelated_matches)
            )

        else:

            evidence = (
                "No recognised environmental/scientific "
                "indicators"
            )

    # Return prediction
    return {
        "relevance_status": status,
        "classification_method": "rule_based",
        "confidence_score": confidence,
        "evidence": evidence
    }
