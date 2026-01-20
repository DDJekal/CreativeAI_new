"""
Job Title Normalizer Service
Bereinigt und normalisiert Stellentitel zu Standard-Berufsbezeichnungen
"""

import re
import logging
import os
from typing import Optional, Dict
import anthropic
import openai

logger = logging.getLogger(__name__)


def clean_job_title_basic(raw_title: str, company_name: str = None) -> str:
    """
    Grundlegende regelbasierte Bereinigung von Stellentiteln
    
    Args:
        raw_title: Roher Stellentitel aus der API
        company_name: Optional Firmenname zum Entfernen
        
    Returns:
        Bereinigter Stellentitel
    """
    title = raw_title.strip()
    
    # Entferne Firmenname falls vorhanden
    if company_name:
        # Entferne verschiedene Varianten
        company_patterns = [
            rf'\b{re.escape(company_name)}\b',
            rf'\b{re.escape(company_name.split()[0])}\b',  # Nur erster Teil
        ]
        for pattern in company_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Entferne typische Füllwörter am Anfang
    prefixes_to_remove = [
        r'^Suchen?\s+(dringend\s+)?',
        r'^Wir suchen\s+',
        r'^Stellenangebot:?\s+',
        r'^Ihre Chance als\s+',
        r'^Werden Sie\s+',
        r'^Verstärken Sie uns als\s+',
        r'^Karriere als\s+',
        r'^für\s+',
        r'^bei\s+',
    ]
    for pattern in prefixes_to_remove:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Entferne "für [Firma]", "bei [Firma]"
    title = re.sub(r'\s+(für|bei|in)\s+[A-ZÄÖÜ][a-zäöüß\s]+(\s+GmbH|\s+AG)?', '', title, flags=re.IGNORECASE)
    
    # Entferne Zeitangaben
    title = re.sub(r'\s+(ab sofort|zum \d+\.\d+\.?|ab \d+\.\d+\.?)', '', title, flags=re.IGNORECASE)
    
    # Entferne Ortsangaben (nur wenn mit "in" eingeleitet)
    title = re.sub(r'\s+in\s+[A-ZÄÖÜ][a-zäöüß]+', '', title)
    
    # Konvertiere häufige Plural-Formen zu Singular
    plural_to_singular = {
        r'\bPflegefachkräfte\b': 'Pflegefachkraft',
        r'\bPflegekräfte\b': 'Pflegekraft',
        r'\bKrankenpfleger(innen)?\b': 'Krankenpfleger',
        r'\bAltenpfleger(innen)?\b': 'Altenpfleger',
        r'\bErzieher(innen)?\b': 'Erzieher',
        r'\bSozialpädagogen\b': 'Sozialpädagoge',
        r'\bPsychotherapeuten\b': 'Psychotherapeut',
        r'\bÄrzte\b': 'Arzt',
        r'\bFachärzte\b': 'Facharzt',
    }
    for pattern, replacement in plural_to_singular.items():
        title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
    
    # Entferne mehrfache Leerzeichen
    title = re.sub(r'\s+', ' ', title)
    
    return title.strip()


class JobTitleNormalizer:
    """
    KI-basierter Stellentitel-Normalizer
    Nutzt Claude (primär) oder OpenAI (fallback) für semantische Normalisierung
    """
    
    def __init__(self):
        """Initialisiert den Normalizer mit API-Clients"""
        self.anthropic_client = None
        self.openai_client = None
        self.cache: Dict[str, str] = {}  # Cache für häufige Titel
        
        # Initialisiere Claude (primär)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            logger.info("JobTitleNormalizer initialized with Claude")
        
        # Fallback: OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and not self.anthropic_client:
            openai.api_key = openai_key
            self.openai_client = openai
            logger.info("JobTitleNormalizer initialized with OpenAI (fallback)")
        
        if not self.anthropic_client and not self.openai_client:
            logger.warning("JobTitleNormalizer: No API key found, will use basic cleaning only")
    
    async def normalize_job_title(self, raw_title: str, company_name: str = None) -> str:
        """
        Normalisiert einen Stellentitel zu einer Standard-Berufsbezeichnung
        
        Bei mehreren Titeln (z.B. "Pflegefachkraft / Altenpfleger") wird der erste zurückgegeben.
        Nutze normalize_job_titles() um alle Varianten zu erhalten.
        
        Args:
            raw_title: Roher Stellentitel aus der API
            company_name: Optional Firmenname zum Entfernen
            
        Returns:
            Normalisierter Stellentitel (ohne m/w/d)
        """
        titles = await self.normalize_job_titles(raw_title, company_name)
        return titles[0]
    
    async def normalize_job_titles(self, raw_title: str, company_name: str = None) -> list[str]:
        """
        Normalisiert Stellentitel und gibt ALLE Varianten zurück bei Doppel-Titeln
        
        Args:
            raw_title: Roher Stellentitel aus der API
            company_name: Optional Firmenname zum Entfernen
            
        Returns:
            Liste von normalisierten Stellentiteln (ohne m/w/d)
            
        Beispiele:
            "Pflegefachkraft / Altenpfleger" → ["Pflegefachkraft", "Altenpfleger"]
            "Erzieher" → ["Erzieher"]
            "Steinburg Pflegefachkräfte" → ["Pflegefachkraft"]
        """
        
        # Stufe 1: Basis-Bereinigung (inkl. Firmennamen-Entfernung)
        title = clean_job_title_basic(raw_title, company_name)
        
        # Cache-Check (für Single-Titel)
        if title in self.cache:
            cached = self.cache[title]
            if isinstance(cached, list):
                return cached
            return [cached]
        
        # Prüfe ob Doppel-Titel (mit "/" oder "oder")
        has_multiple = ' / ' in title or ' oder ' in title.lower()
        
        if has_multiple:
            # Splitte in mehrere Titel
            parts = re.split(r'\s+/\s+|\s+oder\s+', title, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]
            
            # Normalisiere jeden einzeln
            normalized_titles = []
            for part in parts:
                # Entferne (m/w/d) aus jedem Teil
                part_clean = re.sub(r'\s*\([mwdx/]+\)', '', part, flags=re.IGNORECASE)
                part_clean = part_clean.strip()
                
                if not part_clean:
                    continue
                
                # Wenn kein API-Client verfügbar, nutze Fallback
                if not self.anthropic_client and not self.openai_client:
                    normalized = self._fallback_normalize(part_clean)
                else:
                    try:
                        if self.anthropic_client:
                            normalized = await self._normalize_with_claude(part_clean)
                        else:
                            normalized = await self._normalize_with_openai(part_clean)
                    except Exception as e:
                        logger.error(f"JobTitle normalization failed for '{part_clean}': {e}")
                        normalized = self._fallback_normalize(part_clean)
                
                if normalized and normalized not in normalized_titles:
                    normalized_titles.append(normalized)
            
            # Cache speichern
            self.cache[title] = normalized_titles
            logger.info(f"JobTitles normalized (multiple): '{raw_title}' -> {normalized_titles}")
            
            return normalized_titles if normalized_titles else [self._fallback_normalize(title)]
        
        # Single-Titel: Wie bisher
        if not self.anthropic_client and not self.openai_client:
            normalized = self._fallback_normalize(title)
        else:
            try:
                if self.anthropic_client:
                    normalized = await self._normalize_with_claude(title)
                else:
                    normalized = await self._normalize_with_openai(title)
            except Exception as e:
                logger.error(f"JobTitle normalization failed: {e}")
                normalized = self._fallback_normalize(title)
        
        # Cache speichern
        self.cache[title] = [normalized]
        logger.info(f"JobTitle normalized (single): '{raw_title}' -> '{normalized}'")
        
        return [normalized]
    
    async def _normalize_with_claude(self, title: str) -> str:
        """Normalisiert mit Claude API (für einen einzelnen Titel)"""
        prompt = f"""Normalisiere den folgenden Stellentitel zu einer Standard-Berufsbezeichnung.

REGELN:
1. Entferne Marketing-Sprache ("Ihre Chance", "Wir suchen", "Werden Sie")
2. Entferne Zeitangaben ("ab sofort", "zum 01.01.")
3. Entferne Ortsangaben und Firmennamen
4. Nutze offizielle Berufsbezeichnungen (z.B. "Gesundheits- und Krankenpfleger" statt "Krankenpfleger")
5. Entferne (m/w/d), (w/m/d), etc. - das wird später hinzugefügt
6. WICHTIG: Nutze SINGULAR-Form (Pflegefachkraft statt Pflegefachkräfte, Erzieher statt Erzieher*innen)
7. WICHTIG: Wenn der Titel "/" oder "oder" enthält, normalisiere NUR den gegebenen Teil!
8. Behalte Fachrichtungen bei (z.B. "Psychotherapeut für Kinder und Jugendliche")
9. Ausgabe NUR der normalisierte Titel, keine Erklärungen

BEISPIELE:
"Steinburg Pflegefachkräfte (m/w/d)" → "Pflegefachkraft"
"Krankenpfleger*innen in Berlin" → "Gesundheits- und Krankenpfleger"
"Erzieher/innen ab sofort" → "Erzieher"
"Sozialpädagogen für Jugendhilfe" → "Sozialpädagoge für Jugendhilfe"
"Altenpflegerinnen" → "Altenpfleger"

EINGABE: "{title}"
AUSGABE:"""

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        normalized = response.content[0].text.strip()
        normalized = normalized.strip('"').strip("'").strip()
        
        return normalized
    
    async def _normalize_with_openai(self, title: str) -> str:
        """Normalisiert mit OpenAI API (Fallback)"""
        prompt = f"""Normalisiere den folgenden Stellentitel zu einer Standard-Berufsbezeichnung.

REGELN:
1. Entferne Marketing-Sprache
2. Entferne Zeitangaben und Ortsangaben
3. Nutze offizielle Berufsbezeichnungen
4. Entferne (m/w/d)
5. Nutze Singular-Form
6. Bei Doppel-Titeln: Wähle den präziseren

BEISPIELE:
"Suchen Pflegefachkraft (m/w/d)" → "Pflegefachkraft"
"Krankenpfleger in Berlin" → "Gesundheits- und Krankenpfleger"

EINGABE: "{title}"
AUSGABE (nur der Titel):"""

        response = await self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1
        )
        
        normalized = response.choices[0].message.content.strip()
        normalized = normalized.strip('"').strip("'").strip()
        
        return normalized
    
    def _fallback_normalize(self, title: str) -> str:
        """
        Fallback-Normalisierung ohne KI (nur regelbasiert)
        """
        # Entferne (m/w/d) Varianten
        title = re.sub(r'\s*\([mwdx/]+\)', '', title, flags=re.IGNORECASE)
        
        # Entferne Slash-Konstrukte wie "Erzieher/in"
        title = re.sub(r'/in\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'/er\b', '', title, flags=re.IGNORECASE)
        
        # Bei Doppel-Titeln: Nimm den ersten (meist der offizielle)
        if ' / ' in title or ' oder ' in title:
            parts = re.split(r'\s+/\s+|\s+oder\s+', title)
            title = parts[0].strip()
        
        return title.strip()


# Singleton-Instanz
_normalizer_instance: Optional[JobTitleNormalizer] = None


def get_normalizer() -> JobTitleNormalizer:
    """
    Gibt Singleton-Instanz des Normalizers zurück
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = JobTitleNormalizer()
    return _normalizer_instance
