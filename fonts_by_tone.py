# fonts_by_tone.py
# All fonts sourced exclusively from the approved font library.
# Categorized by the 5 brand tones available in the app.
# The AI will pick 3 fonts from the matching tone category.

# Tone -> Font List mapping
# Tones: Minimalist | Professional | Luxury | Bold | Playful

FONTS_BY_TONE = {
    "Minimalist": [
        "Helvetica",
        "Futura",
        "Gill Sans",
        "Myriad",
        "Akzidenz Grotesk",
        "Frutiger",
        "Calibry",
        "Verdana",
        "Corbel",
        "Candara",
        "Arial",
        "News Gothic",
    ],
    "Professional": [
        "Times New Roman",
        "Georgia",
        "Cambria",
        "Garamond",
        "Palatino Linotype",
        "Book Antiqua",
        "Minion",
        "Franklin Gothic",
        "Baskerville",
        "Century",
        "Perpetua",
        "Sabon",
        "Mrs Eaves",
        "Lucida Bright",
    ],
    "Luxury": [
        "Bodoni",
        "Didot",
        "Bembo",
        "Bell MT",
        "Californian FB",
        "Monotype Corsiva",
        "Calligraphy",
        "Rockwell",
        "Snowdrift Regular",
        "Hombre",
        "Perpetua",
        "Sabon",
    ],
    "Bold": [
        "Agency",
        "Elephant",
        "Rockwell",
        "Franklin Gothic",
        "Algerian",
        "Fascinate",
        "Nasalization",
        "Steppes TT",
        "Brandish",
        "Calvin",
        "LCD Mono",
        "Consolas",
        "Courier",
    ],
    "Playful": [
        "Comic Sans MS",
        "Fascinate",
        "Brandish",
        "Calvin",
        "Snowdrift Regular",
        "Hombre",
        "Nasalization",
        "Steppes TT",
        "Calligraphy",
        "Monotype Corsiva",
        "Algerian",
        "LCD Mono",
    ],
}

def get_fonts_for_tone(tone: str) -> list:
    """
    Returns the list of approved fonts for a given tone.
    Falls back to Professional if the tone is not found.
    """
    return FONTS_BY_TONE.get(tone, FONTS_BY_TONE["Professional"])

def get_fonts_str_for_tone(tone: str) -> str:
    """
    Returns a comma-separated string of font names for a given tone.
    Used for injecting into AI prompts.
    """
    fonts = get_fonts_for_tone(tone)
    return ", ".join(fonts)
