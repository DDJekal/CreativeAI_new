"""
Wettbewerbsanalyse Parser
Extrahiert strukturierte Daten aus Wettbewerbsanalyse-Texten
"""

import re
from typing import List, Optional, Dict
from pydantic import BaseModel


class ParsedPersona(BaseModel):
    """Geparste Persona-Daten"""
    name: str
    values: str
    pain: str
    hook: str


class ParsedAnalysis(BaseModel):
    """Vollständige geparste Wettbewerbsanalyse"""
    company_name: str
    location: str
    job_title: str
    personas: List[ParsedPersona]


class CompetitionAnalysisParser:
    """Parser für Wettbewerbsanalyse-Texte"""
    
    def parse(self, text: str) -> ParsedAnalysis:
        """
        Parst Wettbewerbsanalyse-Text und extrahiert:
        - Unternehmen & Standort
        - Job-Titel
        - Personas (Name, Werte, Pain, Hook)
        """
        # Unternehmen & Standort
        company_name = self._extract_company_name(text)
        location = self._extract_location(text)
        job_title = self._extract_job_title(text)
        
        # Personas extrahieren
        personas = self._extract_personas(text)
        
        return ParsedAnalysis(
            company_name=company_name,
            location=location,
            job_title=job_title or "Pflegefachkraft (m/w/d)",
            personas=personas
        )
    
    def _extract_company_name(self, text: str) -> str:
        """Extrahiert Unternehmensnamen"""
        # Pattern: "Wettbewerbsanalyse – [COMPANY NAME]"
        match = re.search(r'Wettbewerbsanalyse\s*[–-]\s*([^\n,]+?)(?:\s*,|\s*\n|Standort)', text)
        if match:
            company = match.group(1).strip()
            # Entferne trailing "GmbH", "gGmbH" etc. für saubereren Namen
            company = re.sub(r'\s+(GmbH|gGmbH|gGmbH,|AG|e\.\s*V\.).*$', '', company)
            return company
        
        return "Unbekanntes Unternehmen"
    
    def _extract_location(self, text: str) -> str:
        """Extrahiert Standort"""
        # Pattern 1: "Standort: [LOCATION]"
        match = re.search(r'Standort:\s*([^\n]+)', text)
        if match:
            location = match.group(1).strip()
            # Entferne trailing "(Bundesland)"
            location = re.sub(r'\s*\([^)]+\).*$', '', location)
            return location
        
        # Pattern 2: Aus Überschrift "COMPANY NAME, Standort LOCATION"
        match = re.search(r'Standort\s+([A-Za-zäöüÄÖÜß\s\-+]+?)(?:\n|$|\|)', text)
        if match:
            return match.group(1).strip()
        
        return "Unbekannter Standort"
    
    def _extract_job_title(self, text: str) -> Optional[str]:
        """Extrahiert Job-Titel/Rolle"""
        # Pattern: "Rolle: [JOB TITLE]"
        match = re.search(r'Rolle(?:\s+\(Gehalt\))?:\s*([^\n]+)', text)
        if match:
            job = match.group(1).strip()
            # Entferne trailing Klammern
            job = re.sub(r'\s*\([^)]*\)\s*$', '', job)
            
            # Normalisiere gängige Abkürzungen
            if "PFK" in job or "Pflegefachkraft" in job:
                return "Pflegefachkraft (m/w/d)"
            elif "HEP" in job or "Heilerziehungspfleger" in job:
                return "Heilerziehungspfleger:in (m/w/d)"
            elif "Servicetechniker" in job or "Elektriker" in job:
                return "Servicetechniker / Elektriker SHK (m/w/d)"
            
            return job
        
        return None
    
    def _extract_personas(self, text: str) -> List[ParsedPersona]:
        """Extrahiert alle Personas"""
        personas = []
        
        # Pattern: Persona-Blöcke - flexibler für verschiedene Anführungszeichen
        # Suche nach "Persona X – [NAME]" (mit verschiedenen Anführungszeichen)
        persona_pattern = r'Persona\s+\d+\s*[–-]\s*[„"\'"]([^""\'"\n]+)[""\'"]'
        
        # Finde alle Persona-Überschriften
        persona_matches = list(re.finditer(persona_pattern, text, re.MULTILINE))
        
        for i, match in enumerate(persona_matches):
            name = match.group(1).strip()
            start_pos = match.end()
            
            # Endposition: Entweder nächste Persona oder Textende
            if i + 1 < len(persona_matches):
                end_pos = persona_matches[i + 1].start()
            else:
                end_pos = len(text)
            
            content = text[start_pos:end_pos].strip()
            
            # Extrahiere Werte, Pain, Hook
            values = self._extract_field(content, r'Wert\s+legt\s+auf:\s*([^\n]+)')
            pain = self._extract_field(content, r'Pain:\s*([^\n]+)')
            
            # Hook mit verschiedenen Anführungszeichen
            hook = (
                self._extract_field(content, r'Hook:\s*[„"]([^""]+)["""]') or
                self._extract_field(content, r'Hook:\s*[\'"]([^\'"]+)[\'"]') or
                self._extract_field(content, r'Hook:\s*[""]([^""]+)[""]')
            )
            
            if name and hook:
                personas.append(ParsedPersona(
                    name=name,
                    values=values or "Stabilität, Wertschätzung",
                    pain=pain or "Überlastung, fehlende Perspektiven",
                    hook=hook
                ))
        
        return personas
    
    def _extract_field(self, text: str, pattern: str) -> Optional[str]:
        """Extrahiert einzelnes Feld via Regex"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test-Beispiel
    test_text = """
    Wettbewerbsanalyse – Lebenshilfe Bad Tölz-Wolfratshausen gGmbH
    Standort: Bad Tölz-Wolfratshausen
    Rolle: Heilerziehungspfleger:in
    
    5) Personas (3)
    
    Persona 1 – „Die heimatnahe HEP"
    Wert legt auf: Wohnortnähe, feste Teams, Sinn
    Pain: Pendeln nach München, anonyme Großstrukturen
    Hook: „Arbeite nah, wirksam und mit echtem Beziehungskern."
    
    Persona 2 – „Die erfahrene Querwechslerin"
    Wert legt auf: Stabilität, klare Aufgaben, Wertschätzung
    Pain: Überforderung im alten System, fehlende Passung
    Hook: „Deine Erfahrung zählt – wir qualifizieren gezielt nach."
    
    Persona 3 – „Der strukturierte Fachprofi"
    Wert legt auf: Planungssicherheit, Pauschalen, Verlässlichkeit
    Pain: Chaosdienste, ständiger Personalmangel
    Hook: „Ein Plan, ein Team, echte Entlastung – auch im Norden."
    """
    
    parser = CompetitionAnalysisParser()
    result = parser.parse(test_text)
    
    print("=" * 70)
    print("PARSER TEST")
    print("=" * 70)
    print(f"Unternehmen: {result.company_name}")
    print(f"Standort: {result.location}")
    print(f"Job: {result.job_title}")
    print(f"\nAnzahl Personas: {len(result.personas)}")
    
    for i, persona in enumerate(result.personas, 1):
        print(f"\nPersona {i}: {persona.name}")
        print(f"  Werte: {persona.values}")
        print(f"  Pain: {persona.pain}")
        print(f"  Hook: {persona.hook}")
