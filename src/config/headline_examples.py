"""
Few-Shot Headline Examples Library

Kuratierte Beispiele für jede Copywriting-Formel.
Werden im Multiprompt-System für Few-Shot-Learning genutzt.
"""

from typing import List, Dict
from pydantic import BaseModel


class HeadlineExample(BaseModel):
    """Ein Headline-Beispiel mit Erklärung"""
    headline: str
    subline: str
    why_good: str
    score: int  # 1-10
    job_category: str = "allgemein"  # pflege, handwerk, buero, etc.


class FormulaDefinition(BaseModel):
    """Definition einer Copywriting-Formel"""
    name: str
    description: str
    structure: str
    tone: str
    when_to_use: str
    examples: List[HeadlineExample]


# ============================================
# HEADLINE FORMELN MIT BEISPIELEN
# ============================================

COPYWRITING_FORMULAS: Dict[str, FormulaDefinition] = {
    
    "pas": FormulaDefinition(
        name="PAS (Problem-Agitate-Solve)",
        description="Benenne das Problem, verstärke den Schmerz, zeige die Lösung",
        structure="""
1. PROBLEM: Benenne den größten Schmerz der Zielgruppe direkt
2. AGITATE: Verstärke das Gefühl - was passiert wenn sich nichts ändert?
3. SOLVE: Zeige den Job/Arbeitgeber als Befreiung
""",
        tone="direkt, empathisch, lösungsorientiert",
        when_to_use="Wenn Zielgruppe klare Pain Points hat (Überstunden, Stress, Einspringen)",
        examples=[
            HeadlineExample(
                headline="Kein Einspringen mehr. Versprochen.",
                subline="Feste Dienste, festes Team, fester Feierabend.",
                why_good="Spricht direkten Pain an, macht konkretes Versprechen, kurz und knackig",
                score=9,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Schluss mit Dauerstress.",
                subline="Bei uns planst du dein Leben, nicht nur deine Schichten.",
                why_good="Problem wird direkt benannt, Lösung ist konkret und bildlich",
                score=8,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Überstunden? Nicht bei uns.",
                subline="Pünktlich Feierabend ist hier normal.",
                why_good="Negiert den Pain direkt, macht klare Aussage",
                score=8,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Raus aus dem Hamsterrad.",
                subline="Pflege mit Zeit für das, was zählt.",
                why_good="Bildliche Sprache, emotional, zeigt Ausweg",
                score=8,
                job_category="pflege"
            ),
        ]
    ),
    
    "story_hook": FormulaDefinition(
        name="Story Hook",
        description="Erzähle einen Moment, der Identifikation schafft",
        structure="""
1. Beschreibe einen Moment, den die Zielgruppe KENNT
2. Nutze "Du kennst das...", "Der Moment, wenn..." oder impliziere eine Situation
3. Zeige den positiven Gegenentwurf
""",
        tone="warm, vertraut, hoffnungsvoll",
        when_to_use="Wenn emotionale Bindung wichtig ist, bei sinnstiftenden Jobs",
        examples=[
            HeadlineExample(
                headline="Der Moment, wenn du weißt: Hier ist anders.",
                subline="Pflege mit echtem Teamgeist.",
                why_good="Narrative Struktur, weckt Neugier, impliziert positive Erfahrung",
                score=9,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Du kennst das: Wieder mal 12 Tage am Stück.",
                subline="Wir auch. Deswegen machen wir's anders.",
                why_good="Direkte Identifikation, zeigt Verständnis, bietet Alternative",
                score=9,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Erinnerst du dich, warum du angefangen hast?",
                subline="Bei uns kannst du es wieder spüren.",
                why_good="Emotional, erinnert an ursprüngliche Motivation",
                score=8,
                job_category="allgemein"
            ),
        ]
    ),
    
    "pattern_interrupt": FormulaDefinition(
        name="Pattern Interrupt",
        description="Brich Erwartungen, sage etwas Unerwartetes",
        structure="""
1. Starte mit einer überraschenden, unerwarteten Aussage
2. Erkläre die Überraschung mit einem positiven Twist
3. Keine Floskeln, kein Standard
""",
        tone="mutig, überraschend, selbstbewusst",
        when_to_use="Wenn Differenzierung vom Wettbewerb wichtig ist, bei starkem Employer Brand",
        examples=[
            HeadlineExample(
                headline="Wir zahlen nicht am besten.",
                subline="Aber wir halten, was wir versprechen. Und das ist mehr wert.",
                why_good="Überraschender Einstieg, authentisch, differenziert sich",
                score=9,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="17:00 Uhr. Feierabend. Wirklich.",
                subline="Bei uns ist pünktlich gehen normal.",
                why_good="Pattern Interrupt durch ungewöhnliche Kürze, glaubwürdig",
                score=9,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Wir haben keine offenen Stellen.",
                subline="Wir haben Plätze für Menschen, die etwas bewegen wollen.",
                why_good="Kompletter Pattern Break, unterscheidet sich von allen anderen",
                score=8,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Vergiss alles, was du über Pflege gehört hast.",
                subline="Bei uns ist Realität besser als der Ruf.",
                why_good="Provokant, adressiert Branchenimage direkt",
                score=8,
                job_category="pflege"
            ),
        ]
    ),
    
    "socratic_hook": FormulaDefinition(
        name="Socratic Hook",
        description="Stelle eine Frage, die zur Selbstreflexion führt",
        structure="""
1. Stelle eine Frage, die die Person SICH SELBST beantworten muss
2. Die Antwort sollte "Ja, stimmt..." oder "Nein, eigentlich nicht..." sein
3. Die Frage impliziert, dass du eine Lösung hast
""",
        tone="nachdenklich, einladend, ehrlich",
        when_to_use="Wenn Zielgruppe unzufrieden aber unentschlossen ist",
        examples=[
            HeadlineExample(
                headline="Wann hast du zuletzt gelacht auf Arbeit?",
                subline="Bei uns ist das Alltag.",
                why_good="Persönliche Frage, zwingt zur Reflexion, impliziert positive Kultur",
                score=9,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Fühlst du dich noch wertgeschätzt?",
                subline="Bei uns wirst du es wieder.",
                why_good="Emotionale Frage, trifft Pain Point direkt",
                score=8,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Arbeitest du für den Job oder für den Sinn?",
                subline="Hier geht beides.",
                why_good="Philosophische Frage, spricht Sinnsuche an",
                score=8,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Was wäre, wenn Montag nicht mehr schmerzt?",
                subline="Finde es heraus.",
                why_good="Imaginative Frage, malt positives Bild",
                score=7,
                job_category="allgemein"
            ),
        ]
    ),
    
    "future_pacing": FormulaDefinition(
        name="Future Pacing",
        description="Male ein Bild der Zukunft, lass die Person sich dort sehen",
        structure="""
1. Beschreibe einen Zustand in der Zukunft ("Stell dir vor...", "In 6 Monaten...")
2. Mache es konkret und greifbar
3. Zeige, dass dieser Zustand erreichbar ist
""",
        tone="inspirierend, konkret, verlockend",
        when_to_use="Wenn Zielgruppe Hoffnung braucht, bei Aufbau-Situationen",
        examples=[
            HeadlineExample(
                headline="Dein neuer Alltag. Ab Montag.",
                subline="Pünktlich, planbar, mit echtem Team.",
                why_good="Konkret, greifbar, macht Veränderung real",
                score=9,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="Stell dir vor, du freust dich auf Montag.",
                subline="Bei uns ist das möglich.",
                why_good="Future Pacing klassisch, emotional, hoffnungsvoll",
                score=8,
                job_category="allgemein"
            ),
            HeadlineExample(
                headline="In 6 Monaten: Dein Team, deine Station, dein Stolz.",
                subline="Der Aufbau beginnt jetzt.",
                why_good="Konkreter Zeitrahmen, Ownership-Gefühl",
                score=8,
                job_category="pflege"
            ),
            HeadlineExample(
                headline="Dein Feierabend. Pünktlich. Jeden Tag.",
                subline="Stell dir vor, das wäre normal. Bei uns ist es das.",
                why_good="Konkreter Benefit als Zukunftsbild",
                score=9,
                job_category="allgemein"
            ),
        ]
    ),
}


# ============================================
# HELPER FUNKTIONEN
# ============================================

def get_formula(formula_key: str) -> FormulaDefinition:
    """Gibt eine Formel-Definition zurück"""
    return COPYWRITING_FORMULAS.get(formula_key)


def get_examples_for_formula(formula_key: str, job_category: str = None) -> List[HeadlineExample]:
    """
    Gibt Beispiele für eine Formel zurück, optional gefiltert nach Job-Kategorie
    """
    formula = COPYWRITING_FORMULAS.get(formula_key)
    if not formula:
        return []
    
    examples = formula.examples
    
    if job_category:
        # Priorisiere passende Kategorie, aber zeige auch allgemeine
        category_examples = [e for e in examples if e.job_category == job_category]
        general_examples = [e for e in examples if e.job_category == "allgemein"]
        examples = category_examples + general_examples
    
    return examples[:5]  # Max 5 Beispiele


def format_examples_for_prompt(formula_key: str, job_category: str = None) -> str:
    """
    Formatiert Beispiele für den LLM-Prompt
    """
    examples = get_examples_for_formula(formula_key, job_category)
    
    if not examples:
        return "Keine Beispiele verfügbar."
    
    formatted = []
    for i, ex in enumerate(examples, 1):
        formatted.append(f"""
Beispiel {i}:
Headline: "{ex.headline}"
Subline: "{ex.subline}"
Warum gut: {ex.why_good}
""")
    
    return "\n".join(formatted)


def get_all_formula_names() -> List[str]:
    """Gibt alle verfügbaren Formel-Namen zurück"""
    return list(COPYWRITING_FORMULAS.keys())


def detect_job_category(job_title: str) -> str:
    """
    Erkennt die Job-Kategorie aus dem Stellentitel
    """
    job_lower = job_title.lower()
    
    if any(kw in job_lower for kw in ["pflege", "kranken", "alten", "gesundheit", "klinik", "station"]):
        return "pflege"
    elif any(kw in job_lower for kw in ["it", "software", "developer", "entwickler", "devops"]):
        return "it"
    elif any(kw in job_lower for kw in ["handwerk", "elektriker", "mechaniker", "monteur"]):
        return "handwerk"
    elif any(kw in job_lower for kw in ["gastro", "koch", "service", "hotel", "restaurant"]):
        return "gastro"
    elif any(kw in job_lower for kw in ["vertrieb", "sales", "verkauf"]):
        return "vertrieb"
    elif any(kw in job_lower for kw in ["büro", "verwaltung", "office", "sekretariat"]):
        return "buero"
    
    return "allgemein"
