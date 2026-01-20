"""
Motif Scenes Library

Szenen-Variationen für die 6 Content-Typen der Creative-Generierung.
Jedes Creative hat einen festen Typ, aber eine zufällige Szene aus dem Pool.
"""

from typing import List, Dict
from dataclasses import dataclass
import random


@dataclass
class SceneVariant:
    """Eine Szenen-Variante mit allen Details"""
    id: str
    name: str
    prompt: str
    camera_settings: str
    mood_tags: List[str] = None
    
    def __post_init__(self):
        if self.mood_tags is None:
            self.mood_tags = []


# ============================================
# HERO SHOT - Protagonist bei der Arbeit
# ============================================

HERO_SHOT_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="close_up_focus",
        name="Nahaufnahme - Konzentriert",
        prompt="""Close-up professional portrait at work
- Focused, competent expression
- Shallow depth of field, blurred work environment
- Natural concentration, authentic moment
- Warm, professional atmosphere
- Person looks skilled and approachable""",
        camera_settings="Canon EOS R5 85mm f/1.4, shallow DOF, natural window light",
        mood_tags=["focused", "professional", "competent"]
    ),
    SceneVariant(
        id="environmental_context",
        name="Arbeitsumgebung - Kontext",
        prompt="""Environmental portrait in professional workspace
- Person in natural work setting, full context visible
- Modern, well-lit work environment
- Subject slightly off-center, room to breathe
- Shows the quality of the workplace
- Documentary editorial style""",
        camera_settings="Sony A7RV 35mm f/2.0, environmental portrait, balanced exposure",
        mood_tags=["authentic", "contextual", "editorial"]
    ),
    SceneVariant(
        id="action_moment",
        name="Action - Mitten in der Arbeit",
        prompt="""Candid action shot at work
- Person actively performing their job
- Hands-on moment, movement captured
- Genuine concentration, not posed
- Dynamic composition, storytelling
- Documentary photojournalism style""",
        camera_settings="Nikon Z9 24-70mm f/2.8, fast shutter 1/500s, action capture",
        mood_tags=["dynamic", "authentic", "engaged"]
    ),
    SceneVariant(
        id="proud_portrait",
        name="Stolzes Porträt",
        prompt="""Confident professional portrait
- Proud, self-assured expression
- Clean professional background
- Direct camera engagement, slight smile
- Shows competence and approachability
- Editorial magazine quality""",
        camera_settings="Hasselblad X2D 90mm f/2.5, controlled lighting, crisp detail",
        mood_tags=["confident", "proud", "professional"]
    ),
    SceneVariant(
        id="caring_interaction",
        name="Fürsorgliche Interaktion",
        prompt="""Caring one-on-one interaction moment
- Professional engaging with client/patient/colleague
- Genuine empathy and attention visible
- Warm, compassionate atmosphere
- Human connection at its best
- Natural, unposed moment""",
        camera_settings="Canon EOS R6 50mm f/1.2, intimate portrait, soft natural light",
        mood_tags=["caring", "empathetic", "human"]
    ),
    SceneVariant(
        id="equipment_mastery",
        name="Kompetenz mit Werkzeug",
        prompt="""Professional working with specialized equipment
- Skilled hands-on moment
- Tools/equipment prominently featured
- Shows expertise and mastery
- Clean composition, professional setting
- Technical competence visible""",
        camera_settings="Sony A1 50mm f/1.4, sharp focus on hands/equipment, clean background",
        mood_tags=["skilled", "technical", "expert"]
    ),
]


# ============================================
# ARTISTIC - Emotionale Interpretation
# ============================================

ARTISTIC_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="watercolor_soft",
        name="Aquarell - Weich & Warm",
        prompt="""Watercolor painting style, soft and warm
- Flowing brushstrokes, pastel color palette
- Dreamy, gentle atmosphere
- Emotional warmth radiates from the image
- Slightly abstract but recognizable forms
- Hand-painted artistic quality""",
        camera_settings="Artistic rendering: watercolor technique, soft edges, layered washes",
        mood_tags=["soft", "warm", "gentle", "artistic"]
    ),
    SceneVariant(
        id="bold_geometric",
        name="Geometrisch - Bold & Modern",
        prompt="""Bold geometric illustration style
- Strong shapes, clear lines, confident colors
- Modern flat design aesthetic
- Vibrant but professional palette
- Clean, contemporary composition
- Magazine editorial illustration quality""",
        camera_settings="Artistic rendering: vector illustration, bold shapes, clean edges",
        mood_tags=["bold", "modern", "confident", "striking"]
    ),
    SceneVariant(
        id="sketch_authentic",
        name="Sketch - Authentisch & Roh",
        prompt="""Hand-drawn charcoal sketch style
- Raw, authentic strokes
- Visible texture and grain
- Honest, unpolished aesthetic
- Emotional depth through simplicity
- Artist's hand visible in every line""",
        camera_settings="Artistic rendering: charcoal sketch, visible paper texture, organic marks",
        mood_tags=["authentic", "raw", "honest", "artistic"]
    ),
    SceneVariant(
        id="minimalist_lines",
        name="Minimalistisch - Clean & Elegant",
        prompt="""Minimalist line art style, elegant simplicity
- Clean, simple lines, refined aesthetic
- Muted sophisticated color palette
- Professional but artistic
- Timeless, premium quality
- Less is more philosophy""",
        camera_settings="Artistic rendering: minimal line art, elegant composition, refined",
        mood_tags=["elegant", "minimal", "refined", "timeless"]
    ),
    SceneVariant(
        id="neon_modern",
        name="Neon Glow - Futuristisch",
        prompt="""Neon glow aesthetic, futuristic style
- Vibrant neon accents against dark background
- Modern, tech-forward atmosphere
- Dynamic energy and innovation
- Bold color contrasts
- Cyberpunk-inspired but professional""",
        camera_settings="Digital art: neon lighting, glow effects, high contrast, modern",
        mood_tags=["modern", "energetic", "innovative", "bold"]
    ),
    SceneVariant(
        id="collage_editorial",
        name="Collage - Editorial Mix",
        prompt="""Editorial collage style, mixed media
- Layered paper textures, cut-out elements
- Contemporary magazine aesthetic
- Sophisticated composition
- Mix of photography and graphic elements
- Cultured, artistic, premium""",
        camera_settings="Mixed media: photography collage, layered textures, editorial quality",
        mood_tags=["sophisticated", "editorial", "layered", "premium"]
    ),
    SceneVariant(
        id="paper_cut",
        name="Scherenschnitt - Elegant",
        prompt="""Paper cut-out style, layered silhouettes
- Elegant shadow play and depth
- Sophisticated simplicity
- Refined, timeless aesthetic
- Clean shapes, beautiful composition
- Premium craft quality""",
        camera_settings="Artistic rendering: paper cut layers, depth shadows, elegant composition",
        mood_tags=["elegant", "refined", "timeless", "sophisticated"]
    ),
    SceneVariant(
        id="gradient_abstract",
        name="Abstrakte Farbverläufe",
        prompt="""Abstract gradient art, flowing colors
- Smooth color transitions, ethereal atmosphere
- Modern, calming aesthetic
- Professional but creative
- Emotional through color and form
- Premium digital art quality""",
        camera_settings="Digital art: smooth gradients, soft blending, modern abstract",
        mood_tags=["calming", "modern", "ethereal", "creative"]
    ),
]


# ============================================
# TEAM SHOT - Zusammenarbeit
# ============================================

TEAM_SHOT_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="huddle_planning",
        name="Team-Besprechung",
        prompt="""Team huddle, collaborative planning moment
- 3-4 people in close discussion
- Engaged body language, active listening
- Professional but relaxed atmosphere
- Whiteboard or shared workspace visible
- Genuine teamwork in action""",
        camera_settings="Canon EOS R6 35mm f/1.8, environmental group shot, natural office light",
        mood_tags=["collaborative", "engaged", "professional"]
    ),
    SceneVariant(
        id="celebration",
        name="Erfolg feiern",
        prompt="""Team celebrating success together
- High-five, fist bumps, genuine smiles
- Joyful, victorious moment
- Positive energy palpable
- Diverse team, inclusive atmosphere
- Authentic celebration, not staged""",
        camera_settings="Sony A7IV 24mm f/2.0, wide angle group shot, bright natural light",
        mood_tags=["joyful", "victorious", "positive"]
    ),
    SceneVariant(
        id="mentoring",
        name="Mentoring & Einarbeitung",
        prompt="""Mentoring moment, experienced guiding newcomer
- Patient, supportive interaction
- Learning and growth visible
- Warm, encouraging atmosphere
- Two people, close collaboration
- Knowledge transfer in action""",
        camera_settings="Nikon Z6II 50mm f/1.4, intimate two-person portrait, soft light",
        mood_tags=["supportive", "growth", "patient"]
    ),
    SceneVariant(
        id="casual_break",
        name="Informelle Pause",
        prompt="""Casual break moment, team relaxing together
- Coffee break or lunch area
- Relaxed, friendly conversation
- Genuine laughter and connection
- Work-life balance visible
- Comfortable, human moment""",
        camera_settings="Fuji X-T5 23mm f/1.4, candid group shot, natural ambient light",
        mood_tags=["relaxed", "friendly", "human"]
    ),
    SceneVariant(
        id="collaborative_work",
        name="Gemeinsam arbeiten",
        prompt="""Team working together on shared task
- Focused collaboration, side-by-side
- Shared screen or workspace
- Productive, efficient atmosphere
- Mutual respect and cooperation
- Professional teamwork""",
        camera_settings="Sony A7C 35mm f/1.8, environmental team shot, balanced lighting",
        mood_tags=["focused", "collaborative", "efficient"]
    ),
    SceneVariant(
        id="diverse_group",
        name="Vielfältiges Team-Porträt",
        prompt="""Diverse team portrait, inclusive group
- 4-6 people, diverse ages and backgrounds
- Confident, professional group stance
- Unified but celebrating differences
- Modern workplace inclusivity
- Editorial team photo quality""",
        camera_settings="Canon EOS R5 50mm f/2.0, formal group portrait, studio-style lighting",
        mood_tags=["inclusive", "diverse", "professional", "unified"]
    ),
]


# ============================================
# LIFESTYLE - Work-Life-Balance
# ============================================

LIFESTYLE_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="park_family",
        name="Familie im Park",
        prompt="""Happy family moment in beautiful park
- Parent with child, genuine joy and connection
- Golden hour sunlight, lush greenery
- Playful, carefree atmosphere
- Authentic candid moment
- Shows the precious time work enables""",
        camera_settings="Sony A7RV 50mm f/1.4, golden hour, dreamy natural bokeh",
        mood_tags=["joyful", "family", "carefree", "precious"]
    ),
    SceneVariant(
        id="cafe_solo",
        name="Entspannt im Café",
        prompt="""Relaxed solo moment in cozy café
- Person enjoying coffee and a book/phone
- Warm interior, soft natural light through windows
- Content, peaceful expression
- Self-care and me-time visible
- Urban lifestyle aesthetic""",
        camera_settings="Fuji X-T5 35mm f/1.4, warm color grade, café ambiance",
        mood_tags=["peaceful", "self-care", "content", "relaxed"]
    ),
    SceneVariant(
        id="sports_active",
        name="Sport & Fitness",
        prompt="""Active lifestyle moment, sports or fitness
- Person running, yoga, or gym activity
- Energetic, healthy, vital atmosphere
- Achievement and wellbeing visible
- Outdoor or modern fitness setting
- Motivational sports photography""",
        camera_settings="Nikon Z9 70-200mm f/2.8, action sports, fast shutter, dynamic",
        mood_tags=["energetic", "healthy", "active", "vital"]
    ),
    SceneVariant(
        id="home_cozy",
        name="Gemütlich zuhause",
        prompt="""Cozy moment at home, personal sanctuary
- Relaxed on comfortable sofa or reading nook
- Warm, intimate lighting, personal touches
- True comfort and rest
- Home as a safe haven
- Hygge lifestyle aesthetic""",
        camera_settings="Canon EOS R6 35mm f/1.4, warm home lighting, intimate ambiance",
        mood_tags=["cozy", "comfortable", "restful", "safe"]
    ),
    SceneVariant(
        id="friends_social",
        name="Mit Freunden",
        prompt="""Social moment with friends, genuine connection
- Group of 3-4 friends laughing together
- Restaurant, bar, or outdoor gathering
- Authentic joy and friendship
- Rich social life and relationships
- Lifestyle magazine quality""",
        camera_settings="Sony A7C 35mm f/1.8, candid group shot, natural mixed lighting",
        mood_tags=["social", "joyful", "connected", "friendship"]
    ),
    SceneVariant(
        id="hobby_passion",
        name="Hobby & Leidenschaft",
        prompt="""Person engaged in hobby or passion project
- Creative pursuit: art, music, crafts, gardening
- Flow state, genuine absorption
- Personal fulfillment visible
- What work-life balance enables
- Documentary lifestyle photography""",
        camera_settings="Nikon Z6III 50mm f/1.2, environmental portrait, natural light",
        mood_tags=["passionate", "fulfilled", "absorbed", "creative"]
    ),
]


# ============================================
# LOCATION - Standort-Attraktivität
# ============================================

LOCATION_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="skyline_golden",
        name="Stadtpanorama Golden Hour",
        prompt="""City skyline at golden hour
- Recognizable landmarks or city character
- Warm sunset light, magical hour glow
- Inviting, aspirational atmosphere
- Shows the city as attractive place to live
- Travel photography magazine quality""",
        camera_settings="Canon EOS R5 24-70mm f/2.8, golden hour, cityscape",
        mood_tags=["inviting", "aspirational", "warm", "beautiful"]
    ),
    SceneVariant(
        id="historic_charm",
        name="Historische Altstadt",
        prompt="""Historic old town, charming architecture
- Beautiful traditional buildings, cobblestone streets
- Cultural richness and heritage visible
- Inviting, pedestrian-friendly atmosphere
- European travel photography aesthetic
- Makes viewer want to explore""",
        camera_settings="Sony A7RV 16-35mm f/2.8, architecture, natural daylight",
        mood_tags=["charming", "historic", "cultural", "inviting"]
    ),
    SceneVariant(
        id="nature_nearby",
        name="Natur in der Nähe",
        prompt="""Beautiful nature accessible nearby
- Forest, lake, mountains, or park
- Fresh air and natural beauty
- Recreation and escape visible
- Shows quality of life outside work
- Landscape photography, inviting""",
        camera_settings="Nikon Z9 24-120mm f/4, landscape, natural light",
        mood_tags=["natural", "peaceful", "refreshing", "accessible"]
    ),
    SceneVariant(
        id="modern_district",
        name="Modernes Viertel",
        prompt="""Modern urban district, contemporary architecture
- Clean lines, innovative buildings
- Vibrant, forward-looking atmosphere
- Cafés, shops, urban life
- Shows modernity and opportunity
- Architectural photography, dynamic""",
        camera_settings="Fuji GFX100S 32-64mm f/4, modern architecture, clean composition",
        mood_tags=["modern", "vibrant", "innovative", "dynamic"]
    ),
    SceneVariant(
        id="local_life",
        name="Lokales Leben",
        prompt="""Local life scene, authentic community
- Market, street café, or public square
- People enjoying daily life
- Vibrant, welcoming community
- Shows the human side of the location
- Street photography, documentary style""",
        camera_settings="Sony A7C 35mm f/1.8, street photography, candid moments",
        mood_tags=["authentic", "vibrant", "welcoming", "community"]
    ),
    SceneVariant(
        id="aerial_overview",
        name="Luftaufnahme",
        prompt="""Aerial drone view of the region
- Bird's eye perspective, grand overview
- Shows scale and beauty from above
- Impressive, expansive view
- Geographic context and opportunities
- Professional drone photography""",
        camera_settings="DJI Mavic 3 Pro, aerial photography, wide angle",
        mood_tags=["impressive", "expansive", "grand", "contextual"]
    ),
]


# ============================================
# FUTURE - Entwicklung & Karriere
# ============================================

FUTURE_SCENES: List[SceneVariant] = [
    SceneVariant(
        id="career_ladder",
        name="Karriereleiter",
        prompt="""Career advancement visualized, upward trajectory
- Professional looking up/forward with confidence
- Stairs, ladder, or upward perspective
- Growth and opportunity ahead
- Aspirational, motivational atmosphere
- Conceptual but grounded photography""",
        camera_settings="Canon EOS R5 35mm f/1.4, low angle, dynamic perspective",
        mood_tags=["aspirational", "growth", "confident", "forward"]
    ),
    SceneVariant(
        id="learning_growth",
        name="Weiterbildung & Lernen",
        prompt="""Learning and development moment
- Person in training, workshop, or study
- Engaged, growing, absorbing knowledge
- Investment in personal development
- Modern learning environment
- Editorial education photography""",
        camera_settings="Sony A7IV 50mm f/1.8, environmental portrait, natural light",
        mood_tags=["learning", "engaged", "developing", "invested"]
    ),
    SceneVariant(
        id="new_chapter",
        name="Neues Kapitel",
        prompt="""New beginning visualization, door opening
- Threshold moment, stepping into opportunity
- Light streaming in, optimistic atmosphere
- Fresh start, new chapter energy
- Symbolic but relatable
- Conceptual editorial photography""",
        camera_settings="Nikon Z6III 24mm f/1.8, environmental, dramatic lighting",
        mood_tags=["optimistic", "fresh", "opportunity", "beginning"]
    ),
    SceneVariant(
        id="achievement",
        name="Erfolg & Zertifikat",
        prompt="""Achievement moment, certificate or completion
- Person proud with certification or diploma
- Accomplishment and recognition visible
- Professional development milestone
- Celebratory but professional
- Editorial portrait, meaningful moment""",
        camera_settings="Canon EOS R6 85mm f/1.4, portrait, celebratory lighting",
        mood_tags=["proud", "accomplished", "recognized", "milestone"]
    ),
    SceneVariant(
        id="leadership",
        name="Führungsrolle",
        prompt="""Leadership moment, person guiding others
- Confident professional in leadership position
- Team looking to them for guidance
- Authority with approachability
- Shows career progression to leadership
- Corporate editorial photography""",
        camera_settings="Sony A1 50mm f/1.2, environmental leader portrait, professional",
        mood_tags=["confident", "leadership", "authoritative", "guiding"]
    ),
    SceneVariant(
        id="vision_forward",
        name="Blick nach vorne",
        prompt="""Forward-looking vision, gazing at horizon
- Person looking toward future with hope
- Wide open space or landscape ahead
- Possibility and potential visible
- Inspirational, optimistic mood
- Cinematic landscape portrait""",
        camera_settings="Canon EOS R5 35mm f/1.4, cinematic, golden hour horizon",
        mood_tags=["hopeful", "visionary", "optimistic", "inspiring"]
    ),
]


# ============================================
# HELPER FUNCTIONS
# ============================================

# Mapping Content-Typ zu Scene-Pool
SCENE_POOLS: Dict[str, List[SceneVariant]] = {
    "hero_shot": HERO_SHOT_SCENES,
    "artistic": ARTISTIC_SCENES,
    "team_shot": TEAM_SHOT_SCENES,
    "lifestyle": LIFESTYLE_SCENES,
    "location": LOCATION_SCENES,
    "future": FUTURE_SCENES,
}


def get_random_scene(content_type: str) -> SceneVariant:
    """
    Wählt eine zufällige Szene aus dem Pool für den Content-Typ
    
    Args:
        content_type: hero_shot, artistic, team_shot, lifestyle, location, future
        
    Returns:
        SceneVariant mit allen Details
    """
    pool = SCENE_POOLS.get(content_type)
    
    if not pool:
        # Fallback auf hero_shot
        pool = HERO_SHOT_SCENES
    
    return random.choice(pool)


def get_all_scenes(content_type: str) -> List[SceneVariant]:
    """
    Gibt alle verfügbaren Szenen für einen Content-Typ zurück
    
    Args:
        content_type: hero_shot, artistic, team_shot, lifestyle, location, future
        
    Returns:
        Liste aller SceneVariants für diesen Typ
    """
    return SCENE_POOLS.get(content_type, HERO_SHOT_SCENES)


def get_content_types() -> List[str]:
    """Gibt alle verfügbaren Content-Typen zurück"""
    return list(SCENE_POOLS.keys())


def get_scene_count(content_type: str) -> int:
    """Gibt die Anzahl der Szenen für einen Content-Typ zurück"""
    pool = SCENE_POOLS.get(content_type, [])
    return len(pool)
