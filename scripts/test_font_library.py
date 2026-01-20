"""
Test Font Library - Zeigt alle 30 verfügbaren Fonts
"""

import sys
sys.path.insert(0, '.')

from src.config.font_library import (
    FONT_LIBRARY,
    FontCategory,
    FontMood,
    get_fonts_by_category,
    get_fonts_by_mood,
    get_font_pair,
    get_recommended_fonts,
)


def main():
    print("=" * 70)
    print("FONT LIBRARY - 30 professionelle Schriftarten")
    print("=" * 70)
    
    # Alle Fonts nach Kategorie
    print("\n" + "=" * 70)
    print("FONTS NACH KATEGORIE")
    print("=" * 70)
    
    for category in FontCategory:
        fonts = get_fonts_by_category(category)
        if fonts:
            print(f"\n--- {category.value.upper()} ({len(fonts)}) ---")
            for f in fonts:
                moods = ", ".join([m.value for m in f.moods])
                print(f"  [{f.id:18}] {f.name:20} - {f.description[:40]}")
    
    # Font-Paare
    print("\n" + "=" * 70)
    print("EMPFOHLENE FONT-PAARE")
    print("=" * 70)
    
    for mood in [FontMood.BOLD, FontMood.ELEGANT, FontMood.MODERN, FontMood.FRIENDLY, FontMood.PROFESSIONAL]:
        headline, body = get_font_pair(mood)
        print(f"\n{mood.value.upper()}:")
        print(f"  Headline: {headline.name} ({headline.category.value})")
        print(f"  Body:     {body.name} ({body.category.value})")
    
    # Statistik
    print("\n" + "=" * 70)
    print("STATISTIK")
    print("=" * 70)
    print(f"\nTotal Fonts: {len(FONT_LIBRARY)}")
    
    for category in FontCategory:
        count = len(get_fonts_by_category(category))
        print(f"  {category.value:25} {count}")
    
    # Empfehlungen
    print("\n" + "=" * 70)
    print("EMPFEHLUNGEN FUER RECRUITING")
    print("=" * 70)
    
    print("\nFuer PFLEGE / SOZIALES (warm, freundlich):")
    for f in get_recommended_fonts(mood=FontMood.FRIENDLY, limit=3):
        print(f"  - {f.name}: {f.description}")
    
    print("\nFuer TECH / IT (modern, innovativ):")
    for f in get_recommended_fonts(mood=FontMood.MODERN, limit=3):
        print(f"  - {f.name}: {f.description}")
    
    print("\nFuer FINANCE / LAW (serioes, professionell):")
    for f in get_recommended_fonts(mood=FontMood.PROFESSIONAL, limit=3):
        print(f"  - {f.name}: {f.description}")
    
    print("\nFuer HEADLINES (stark, auffaellig):")
    for f in get_fonts_by_category(FontCategory.DISPLAY):
        print(f"  - {f.name}: {f.description}")
    
    print("\n" + "=" * 70)
    print("ALLE FONT IDs (fuer Eingabe)")
    print("=" * 70)
    print("\n" + ", ".join([f.id for f in FONT_LIBRARY]))
    print()


if __name__ == "__main__":
    main()

