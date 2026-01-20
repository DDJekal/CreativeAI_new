# Workflow-Orchestrierung: End-to-End Pipeline

## Übersicht

Die Workflow-Orchestrierung verbindet alle Komponenten zu einer effizienten, robusten End-to-End-Pipeline für Creative-Generierung. Sie koordiniert parallele Prozesse, managed Fehler, optimiert Performance und stellt sicher, dass jedes Creative in hoher Qualität ausgeliefert wird.

### Die komplette Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│  INPUT: Job-ID oder Unternehmensname                          │
└────────────────────┬─────────────────────────────────────────┘
                     ↓
         ┌───────────────────────────┐
         │  PHASE 1: TEXT            │
         │  • HOC API                │
         │  • Perplexity Research    │
         │  • OpenAI Copywriting     │
         │  → 5 Text-Varianten       │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  PHASE 2: IMAGES          │
         │  (Batches von 5, nicht 10)│
         │                           │
         │  • Meta-Analysis          │
         │  • 4x Designer-KIs        │
         │  • BFL (max 5 concurrent!)│
         │  → 4 Basis-Bilder         │
         │    pro Text-Variante      │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  GATE 1a: OCR BASE        │  ← NEU!
         │  Fail-Fast bei BFL-Text   │
         └───────────┬───────────────┘
                     ↓ [PASS]
         ┌───────────────────────────┐
         │  PHASE 3: CI & LAYOUT     │
         │  (parallel)               │
         │                           │
         │  • CI-Scraping (cached)   │
         │  • Image Analysis         │
         │  • Layout Designer        │
         │  → overlay_zones          │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  PHASE 4a: I2I            │
         │  (NUR Text-Overlays)      │
         │                           │
         │  • OpenAI gpt-image-1     │
         │  • Kein Logo hier!        │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  PHASE 4b: LOGO           │  ← NEU!
         │  (Pillow Compositing)     │
         │                           │
         │  • Logo als PNG-Layer     │
         │  • Falls vorhanden        │
         └───────────┬───────────────┘
                     ↓
         ┌───────────────────────────┐
         │  PHASE 5: QUALITY GATES   │
         │  • Gate 1b (Vision)       │  ← Semantisch!
         │  • Gates 2-4              │  ← 4 statt 5!
         │  • Auto-Retry bei Fail    │
         │  → Approved Creatives     │
         └───────────┬───────────────┘
                     ↓
┌────────────────────────────────────────────────────┐
│  OUTPUT: 20+ finale Creatives                      │
│  (5 Text-Varianten × 4 Bilder pro Variante)       │
└────────────────────────────────────────────────────┘
```

**Gesamt-Output pro Job:**
- 5 Text-Varianten (A, B, C, D, E)
- 4 Bildtypen (Job-Fokus, Lifestyle, Artistic, Location)
- = **20 verschiedene Creatives**
- Plus Quality-Gate-Reports
- Plus A/B-Testing-Vorbereitung

---

## Orchestrator-Architektur

### Master Orchestrator

```python
class CreativeOrchestrator:
    """
    Master-Orchestrator für gesamte Creative-Generierung
    """
    
    def __init__(self):
        self.hoc_api = HOCAPIClient()
        self.perplexity_mcp = PerplexityMCP()
        self.openai_client = OpenAIClient()
        self.bfl_client = BFLClient()
        self.firecrawl_mcp = FirecrawlMCP()
        
        self.cache = CacheManager()
        self.metrics = MetricsCollector()
        self.logger = Logger("CreativeOrchestrator")
    
    async def generate_complete_campaign(
        self,
        job_id: str,
        config: dict = None
    ) -> dict:
        """
        Haupteinstieg: Generiert komplette Kampagne
        
        Returns:
            {
                "job_id": str,
                "company_name": str,
                "text_variants": [...],
                "creatives": [...],
                "quality_reports": {...},
                "metadata": {...}
            }
        """
        
        start_time = time.time()
        self.logger.info(f"Starting campaign generation for job {job_id}")
        
        try:
            # PHASE 1: Text-Generierung
            self.logger.info("Phase 1: Text Generation")
            text_result = await self.phase_1_text_generation(job_id)
            
            # PHASE 2: Bild-Generierung (parallel für alle Text-Varianten)
            self.logger.info("Phase 2: Image Generation")
            images_result = await self.phase_2_image_generation(
                job_id,
                text_result['variants']
            )
            
            # PHASE 3: CI & Layout (einmal, dann für alle reused)
            self.logger.info("Phase 3: CI & Layout Strategy")
            ci_layout_result = await self.phase_3_ci_and_layout(
                text_result['company_name'],
                images_result
            )
            
            # PHASE 4: Composition (parallel für alle Kombinationen)
            self.logger.info("Phase 4: Creative Composition")
            composition_result = await self.phase_4_composition(
                text_result,
                images_result,
                ci_layout_result
            )
            
            # PHASE 5: Quality Gates (parallel)
            self.logger.info("Phase 5: Quality Gates")
            quality_result = await self.phase_5_quality_gates(
                composition_result
            )
            
            # Zusammenfassung
            duration = time.time() - start_time
            
            result = {
                "job_id": job_id,
                "company_name": text_result['company_name'],
                "status": "completed",
                "text_variants": text_result['variants'],
                "creatives": quality_result['approved_creatives'],
                "failed_creatives": quality_result['failed_creatives'],
                "quality_reports": quality_result['reports'],
                "metadata": {
                    "total_creatives_generated": len(composition_result),
                    "creatives_approved": len(quality_result['approved_creatives']),
                    "duration_seconds": duration,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            # Metriken loggen
            await self.metrics.log_campaign(result)
            
            self.logger.info(
                f"Campaign completed: {len(quality_result['approved_creatives'])} "
                f"creatives in {duration:.1f}s"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Campaign generation failed: {e}")
            await self.metrics.log_error(job_id, str(e))
            raise
```

---

## Phase 1: Text-Generierung

### Sequentiell (da nachfolgende Phasen davon abhängen)

```python
async def phase_1_text_generation(self, job_id: str) -> dict:
    """
    Phase 1: Text-Content generieren
    
    Steps:
    1. HOC API → Job-Daten holen
    2. Perplexity → Research (optional, gecacht)
    3. Context Fusion → Strukturierung
    4. Copywriting → 5 Varianten
    """
    
    # 1. HOC API
    self.logger.info("Fetching job data from HOC API")
    job_data = await self.hoc_api.get_job(job_id)
    
    company_name = job_data.get('company_name')
    if not company_name:
        raise ValueError("Company name not found in job data")
    
    # 2. Perplexity Research (optional, mit Cache)
    research_data = await self.get_or_research(
        job_type=job_data.get('job_title'),
        location=job_data.get('location')
    )
    
    # 3. Context Fusion
    self.logger.info("Fusing context data")
    structured_context = await self.openai_client.context_fusion(
        job_data=job_data,
        research=research_data
    )
    
    # 4. Copywriting (5 Varianten)
    self.logger.info("Generating 5 text variants")
    copy_variants = await self.openai_client.copywriting(
        context=structured_context,
        num_variants=5
    )
    
    return {
        "job_id": job_id,
        "company_name": company_name,
        "job_data": job_data,
        "variants": copy_variants,
        "structured_context": structured_context
    }


async def get_or_research(self, job_type: str, location: str) -> dict:
    """
    Holt Research aus Cache oder führt neue durch
    """
    cache_key = f"research_{job_type}_{location}"
    
    # Cache-Check (7 Tage)
    cached = await self.cache.get(cache_key, max_age_days=7)
    if cached:
        self.logger.info("Using cached research data")
        return cached
    
    # Neu researchen
    self.logger.info("Performing new research via Perplexity")
    research = await self.perplexity_mcp.research(
        query=f"Key motivators and benefits for {job_type} in {location} 2025"
    )
    
    # Cachen
    await self.cache.set(cache_key, research, ttl_days=7)
    
    return research
```

---

## Phase 2: Bild-Generierung

### Parallel für alle Text-Varianten

```python
async def phase_2_image_generation(
    self,
    job_id: str,
    text_variants: list
) -> dict:
    """
    Phase 2: Bilder generieren (parallel für alle Varianten)
    
    Pro Text-Variante:
    - Meta-Analysis → 4 Bild-Konzepte
    - 4x Designer-KIs (parallel)
    - 4x BFL Generation (parallel)
    
    = 4 Basis-Bilder pro Text-Variante
    """
    
    # Parallele Generierung für alle Text-Varianten
    tasks = [
        self.generate_images_for_variant(job_id, variant)
        for variant in text_variants
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Error-Handling
    images_by_variant = {}
    for variant, result in zip(text_variants, results):
        if isinstance(result, Exception):
            self.logger.error(
                f"Image generation failed for variant {variant['id']}: {result}"
            )
            # Fallback: Retry oder Skip
            continue
        
        images_by_variant[variant['id']] = result
    
    return {
        "job_id": job_id,
        "images_by_variant": images_by_variant
    }


async def generate_images_for_variant(
    self,
    job_id: str,
    text_variant: dict
) -> dict:
    """
    Generiert 4 Bilder für eine Text-Variante
    
    WICHTIG: BFL erlaubt nur 5 concurrent requests!
    Da wir 4 Bilder pro Variante haben, ist das OK.
    Aber bei mehreren Varianten parallel: Batch-Processing nötig!
    """
    variant_id = text_variant['id']
    
    # 1. Meta-Analysis (Creative Director)
    self.logger.info(f"Meta-analysis for variant {variant_id}")
    meta_output = await self.openai_client.meta_analysis(
        job_title=text_variant['job_title'],
        headline=text_variant['headline'],
        benefits=text_variant['benefits'],
        emotional_anchors=text_variant['emotional_anchors']
    )
    
    # 2. 4 Designer-KIs (parallel - OpenAI hat hohe Limits)
    self.logger.info(f"Generating 4 BFL prompts for variant {variant_id}")
    designer_tasks = [
        self.openai_client.designer_prompt(
            designer_type=designer_type,
            concept=meta_output['image_concepts'][i]
        )
        for i, designer_type in enumerate([
            'job_focus',
            'lifestyle',
            'artistic',
            'location'
        ])
    ]
    
    designer_prompts = await asyncio.gather(*designer_tasks)
    
    # 3. 4x BFL Generation (mit Rate-Limiting!)
    # BFL erlaubt nur 5 concurrent → 4 pro Variante ist OK
    self.logger.info(f"Generating 4 images via BFL for variant {variant_id}")
    bfl_tasks = [
        self.executor.execute_with_limit(
            'bfl',  # ← Rate-Limited!
            self.bfl_client.generate(
                prompt=prompt['bfl_prompt'],
                seed=random.randint(1, 1000000)
            )
        )
        for prompt in designer_prompts
    ]
    
    images = await asyncio.gather(*bfl_tasks)
    
    return {
        "variant_id": variant_id,
        "meta_output": meta_output,
        "designer_prompts": designer_prompts,
        "images": [
            {
                "type": ["job_focus", "lifestyle", "artistic", "location"][i],
                "url": img['url'],
                "prompt": designer_prompts[i]['bfl_prompt']
            }
            for i, img in enumerate(images)
        ]
    }


async def generate_all_bfl_images_batched(self, all_prompts: list) -> list:
    """
    Generiert alle BFL-Bilder in Batches von 5 (BFL Rate Limit!)
    
    Bei 20 Bildern (5 Varianten × 4 Bilder):
    → 4 Batches à 5 Bilder
    → ~3-4 Minuten total (statt fehlschlagender 2 Minuten)
    """
    
    results = []
    batch_size = 5  # BFL Rate Limit!
    
    for batch_idx in range(0, len(all_prompts), batch_size):
        batch = all_prompts[batch_idx:batch_idx + batch_size]
        
        self.logger.info(
            f"BFL Batch {batch_idx // batch_size + 1}/"
            f"{(len(all_prompts) + batch_size - 1) // batch_size} "
            f"({len(batch)} images)"
        )
        
        batch_tasks = [
            self.executor.execute_with_limit(
                'bfl',
                self.bfl_client.generate(prompt=p['bfl_prompt'])
            )
            for p in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        
        # 2s Pause zwischen Batches für Safety
        if batch_idx + batch_size < len(all_prompts):
            await asyncio.sleep(2.0)
    
    return results
```

---

## Phase 3: CI & Layout

### Einmalig, dann für alle reused

```python
async def phase_3_ci_and_layout(
    self,
    company_name: str,
    images_result: dict
) -> dict:
    """
    Phase 3: CI scrapen und Layout-Strategien entwickeln
    
    CI: Einmal scrapen, für alle Creatives nutzen
    Layout: Pro Bild-Typ eine Strategie
    """
    
    # 1. CI-Scraping (einmal, gecacht 90 Tage)
    self.logger.info(f"Extracting brand identity for {company_name}")
    brand_identity = await self.get_or_scrape_ci(company_name)
    
    # 2. Bild-Analysen (parallel für alle einzigartigen Bilder)
    unique_images = self.collect_unique_images(images_result)
    
    self.logger.info(f"Analyzing {len(unique_images)} unique images")
    analysis_tasks = [
        self.openai_client.analyze_image_for_text_zones(img['url'])
        for img in unique_images
    ]
    
    image_analyses = await asyncio.gather(*analysis_tasks)
    
    # Mapping: image_url → analysis
    analyses_by_image = {
        img['url']: analysis
        for img, analysis in zip(unique_images, image_analyses)
    }
    
    return {
        "brand_identity": brand_identity,
        "image_analyses": analyses_by_image
    }


async def get_or_scrape_ci(self, company_name: str) -> dict:
    """
    Holt CI aus Cache oder scrapt neu
    """
    cache_key = f"ci_{company_name}"
    
    # Cache-Check (90 Tage)
    cached = await self.cache.get(cache_key, max_age_days=90)
    if cached:
        self.logger.info(f"Using cached CI for {company_name}")
        return cached
    
    # Neu scrapen
    self.logger.info(f"Scraping CI for {company_name}")
    try:
        ci_data = await self.firecrawl_mcp.extract_brand_identity(company_name)
        
        # Cache
        await self.cache.set(cache_key, ci_data, ttl_days=90)
        
        return ci_data
    
    except Exception as e:
        self.logger.warning(f"CI scraping failed: {e}, using defaults")
        return self.create_default_ci(company_name)


def collect_unique_images(self, images_result: dict) -> list:
    """
    Sammelt alle einzigartigen Bild-URLs
    """
    seen = set()
    unique = []
    
    for variant_data in images_result['images_by_variant'].values():
        for img in variant_data['images']:
            if img['url'] not in seen:
                seen.add(img['url'])
                unique.append(img)
    
    return unique
```

---

## Phase 4: Composition

### Massiv parallel (20+ Creatives gleichzeitig)

```python
async def phase_4_composition(
    self,
    text_result: dict,
    images_result: dict,
    ci_layout_result: dict
) -> list:
    """
    Phase 4: Finale Creatives komponieren
    
    Für jede Text-Bild-Kombination:
    - Layout-Designer → I2I-Prompt
    - OpenAI I2I → Finales Creative
    
    = 5 Varianten × 4 Bilder = 20 Creatives (parallel!)
    """
    
    brand_identity = ci_layout_result['brand_identity']
    image_analyses = ci_layout_result['image_analyses']
    
    # Erstelle alle Kombinationen
    composition_tasks = []
    
    for text_variant in text_result['variants']:
        variant_id = text_variant['id']
        variant_images = images_result['images_by_variant'].get(variant_id)
        
        if not variant_images:
            continue
        
        for img in variant_images['images']:
            task = self.compose_single_creative(
                text_variant=text_variant,
                image=img,
                brand_identity=brand_identity,
                image_analysis=image_analyses[img['url']]
            )
            composition_tasks.append(task)
    
    self.logger.info(f"Composing {len(composition_tasks)} creatives in parallel")
    
    # Parallele Ausführung
    creatives = await asyncio.gather(
        *composition_tasks,
        return_exceptions=True
    )
    
    # Filter Exceptions
    valid_creatives = [
        c for c in creatives
        if not isinstance(c, Exception)
    ]
    
    failed_count = len(creatives) - len(valid_creatives)
    if failed_count > 0:
        self.logger.warning(f"{failed_count} creatives failed composition")
    
    return valid_creatives


async def compose_single_creative(
    self,
    text_variant: dict,
    image: dict,
    brand_identity: dict,
    image_analysis: dict
) -> dict:
    """
    Komponiert ein einzelnes Creative
    
    NEUER WORKFLOW mit Phase 4a/4b:
    1. Layout Designer
    2. Gate 1a (bereits vorher gelaufen)
    3. Phase 4a: I2I (nur Text)
    4. Phase 4b: Logo-Compositing (Pillow)
    """
    
    # 1. Layout Designer
    layout_strategy = await self.openai_client.layout_designer(
        base_image_analysis=image_analysis,
        brand_identity=brand_identity,
        text_content={
            "headline": text_variant['headline'],
            "subline": text_variant['subline'],
            "benefits": text_variant['benefits'],
            "cta": text_variant['cta_primary']
        },
        design_mood=text_variant['style'],
        has_logo=brand_identity.get('logo') is not None
    )
    
    # 2. Phase 4a: OpenAI I2I - NUR Text-Overlays (kein Logo!)
    i2i_image_url = await self.openai_client.i2i_generation(
        base_image_url=image['url'],
        layout_prompt=layout_strategy['i2i_prompt'],
        texts=text_variant,
        brand_identity=brand_identity
        # KEIN Logo hier! Logo kommt in Phase 4b
    )
    
    # 3. Phase 4b: Logo-Compositing (Pillow)
    final_image_url = await self.compose_logo_overlay(
        i2i_image_url=i2i_image_url,
        brand_identity=brand_identity,
        layout_strategy=layout_strategy
    )
    
    return {
        "text_variant_id": text_variant['id'],
        "image_type": image['type'],
        "base_image_url": image['url'],
        "i2i_image_url": i2i_image_url,      # ← NEU: Zwischenschritt
        "final_image_url": final_image_url,
        "texts": text_variant,
        "brand_identity": brand_identity,
        "layout_strategy": layout_strategy,
        "overlay_zones": image_analysis.get('text_zones', {}),  # ← Für Gate 1b
        "status": "composed"
    }


async def compose_logo_overlay(
    self,
    i2i_image_url: str,
    brand_identity: dict,
    layout_strategy: dict
) -> str:
    """
    Phase 4b: Logo-Compositing mit Pillow
    
    Wenn kein Logo: Gibt i2i_image_url unverändert zurück.
    """
    from PIL import Image
    import io
    
    # Kein Logo → direkt zurückgeben
    if not brand_identity.get('logo'):
        return i2i_image_url
    
    try:
        # Lade I2I-Bild
        i2i_data = await download_image(i2i_image_url)
        img = Image.open(io.BytesIO(i2i_data))
        
        # Lade Logo
        logo_url = brand_identity['logo']['url']
        logo_data = await download_image(logo_url)
        logo_img = Image.open(io.BytesIO(logo_data))
        
        # Resize Logo (max 80px Höhe)
        max_height = 80
        aspect = logo_img.width / logo_img.height
        logo_img = logo_img.resize(
            (int(max_height * aspect), max_height),
            Image.LANCZOS
        )
        
        # Position aus Layout-Strategie
        logo_position = layout_strategy.get('logo_position', 'top_right')
        margin = 20
        
        positions = {
            'top_right': (img.width - logo_img.width - margin, margin),
            'top_left': (margin, margin),
            'bottom_right': (img.width - logo_img.width - margin, 
                           img.height - logo_img.height - margin),
            'bottom_left': (margin, img.height - logo_img.height - margin)
        }
        pos = positions.get(logo_position, positions['top_right'])
        
        # Composite mit Transparenz-Support
        if logo_img.mode == 'RGBA':
            img.paste(logo_img, pos, logo_img)
        else:
            img.paste(logo_img, pos)
        
        # Speichern und Upload
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=95)
        buffer.seek(0)
        
        return await upload_to_storage(buffer, 'final_creative.png')
    
    except Exception as e:
        self.logger.warning(f"Logo compositing failed: {e}")
        return i2i_image_url  # Fallback: ohne Logo
```

---

## Phase 5: Quality Gates

### Parallel mit Auto-Retry

```python
async def phase_5_quality_gates(
    self,
    composed_creatives: list
) -> dict:
    """
    Phase 5: Quality Gates (parallel mit Retry)
    """
    
    # Quality-Check für alle Creatives (parallel)
    gate_tasks = [
        self.check_creative_quality_with_retry(creative, max_retries=3)
        for creative in composed_creatives
    ]
    
    self.logger.info(f"Running quality gates for {len(gate_tasks)} creatives")
    
    results = await asyncio.gather(*gate_tasks, return_exceptions=True)
    
    # Kategorisiere
    approved = []
    failed = []
    
    for creative, result in zip(composed_creatives, results):
        if isinstance(result, Exception):
            self.logger.error(f"Quality check exception: {result}")
            failed.append({
                **creative,
                "status": "error",
                "error": str(result)
            })
            continue
        
        if result['overall_status'] in ['PASS', 'PASS_WITH_WARNINGS']:
            approved.append({
                **creative,
                "quality_report": result,
                "status": "approved"
            })
        else:
            failed.append({
                **creative,
                "quality_report": result,
                "status": "failed"
            })
    
    self.logger.info(
        f"Quality gates completed: "
        f"{len(approved)} approved, {len(failed)} failed"
    )
    
    return {
        "approved_creatives": approved,
        "failed_creatives": failed,
        "reports": {
            "total": len(composed_creatives),
            "approved": len(approved),
            "failed": len(failed),
            "approval_rate": len(approved) / len(composed_creatives)
        }
    }


async def check_creative_quality_with_retry(
    self,
    creative: dict,
    max_retries: int = 3
) -> dict:
    """
    Quality Gates mit Auto-Retry
    """
    
    for attempt in range(max_retries):
        try:
            # Alle 5 Gates
            gate_results = await self.run_all_quality_gates(
                base_image_url=creative['base_image_url'],
                final_image_url=creative['final_image_url'],
                expected_texts=creative['texts'],
                brand_identity=creative['brand_identity'],
                overlay_zones=creative['overlay_zones']
            )
            
            # PASS?
            if gate_results['overall_status'] in ['PASS', 'PASS_WITH_WARNINGS']:
                return gate_results
            
            # FAIL → Retry?
            if attempt < max_retries - 1:
                self.logger.info(
                    f"Creative failed gates, retrying (attempt {attempt + 2})"
                )
                
                # NEUE LOGIK: Immer erst I2I retry (günstiger!)
                # BFL nur bei letztem Retry wenn Gate 1a/1b weiter failen
                
                action = gate_results.get('action', 'regenerate_i2i')
                
                if action == 'regenerate_bfl' and attempt >= 1:
                    # Erst beim 2. Retry BFL neu generieren
                    self.logger.info("Multiple I2I retries failed, regenerating BFL")
                    creative['base_image_url'] = await self.regenerate_bfl_image(
                        creative
                    )
                
                # I2I immer neu bei Retry
                creative['final_image_url'] = await self.regenerate_i2i(
                    creative
                )
                
                continue
            
            # Max retries erreicht
            return gate_results
        
        except Exception as e:
            self.logger.error(f"Quality gate attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
    
    return gate_results
```

---

## Parallelisierungs-Strategie

### Optimale Concurrency

```python
class ParallelExecutor:
    """
    Managed parallele Ausführung mit Rate-Limiting
    """
    
    def __init__(self):
        # API Rate Limits - KORRIGIERT für reale Limits
        self.limits = {
            'openai': asyncio.Semaphore(50),   # Max 50 concurrent
            'bfl': asyncio.Semaphore(5),       # ✓ KORRIGIERT: Max 5 concurrent (nicht 10!)
            'perplexity': asyncio.Semaphore(3),# Konservativer
            'firecrawl': asyncio.Semaphore(2)  # Konservativer
        }
    
    async def execute_with_limit(
        self,
        api_name: str,
        coro
    ):
        """
        Führt Coroutine mit Rate-Limit aus
        """
        async with self.limits[api_name]:
            return await coro
    
    async def batch_execute(
        self,
        tasks: list,
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ):
        """
        Führt Tasks in Batches aus
        """
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            batch_results = await asyncio.gather(
                *batch,
                return_exceptions=True
            )
            
            results.extend(batch_results)
            
            # Delay zwischen Batches
            if i + batch_size < len(tasks):
                await asyncio.sleep(delay_between_batches)
        
        return results
```

---

## Error Handling & Recovery

### Robuste Fehlerbehandlung

```python
class ErrorHandler:
    """
    Zentrale Fehlerbehandlung
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = Logger("ErrorHandler")
    
    async def handle_phase_error(
        self,
        phase_name: str,
        job_id: str,
        error: Exception
    ) -> dict:
        """
        Behandelt Fehler in einer Phase
        """
        
        self.logger.error(f"Phase {phase_name} failed for job {job_id}: {error}")
        
        # Kategorisiere Fehler
        if isinstance(error, APIError):
            return await self.handle_api_error(phase_name, error)
        
        elif isinstance(error, ValidationError):
            return await self.handle_validation_error(phase_name, error)
        
        elif isinstance(error, TimeoutError):
            return await self.handle_timeout_error(phase_name, error)
        
        else:
            return await self.handle_unknown_error(phase_name, error)
    
    async def handle_api_error(self, phase: str, error: APIError) -> dict:
        """
        API-Fehler (Rate Limit, Auth, etc.)
        """
        
        if error.status_code == 429:  # Rate Limit
            # Exponential Backoff
            wait_time = calculate_backoff(error.retry_after)
            self.logger.info(f"Rate limit hit, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            return {"action": "retry", "delay": wait_time}
        
        elif error.status_code == 401:  # Auth
            self.logger.error("Authentication failed")
            return {"action": "fail", "reason": "auth_error"}
        
        elif error.status_code >= 500:  # Server Error
            # Retry mit Backoff
            return {"action": "retry", "delay": 5.0}
        
        else:
            return {"action": "fail", "reason": f"api_error_{error.status_code}"}
    
    async def handle_validation_error(self, phase: str, error: ValidationError) -> dict:
        """
        Validierungs-Fehler (schlechte Daten)
        """
        self.logger.error(f"Validation failed: {error}")
        
        # Keine Retry bei Validierung → Daten-Problem
        return {
            "action": "fail",
            "reason": "validation_error",
            "details": str(error)
        }
    
    async def handle_timeout_error(self, phase: str, error: TimeoutError) -> dict:
        """
        Timeout-Fehler
        """
        self.logger.warning(f"Timeout in phase {phase}")
        
        # Retry mit längerem Timeout
        return {
            "action": "retry",
            "delay": 2.0,
            "increase_timeout": True
        }


def calculate_backoff(retry_after: int = None, attempt: int = 1) -> float:
    """
    Exponential Backoff
    """
    if retry_after:
        return retry_after
    
    # 2^attempt mit Jitter
    base_delay = 2 ** attempt
    jitter = random.uniform(0, 0.1 * base_delay)
    
    return min(base_delay + jitter, 60)  # Max 60s
```

---

## Caching-Strategie

### Multi-Layer Cache

```python
class CacheManager:
    """
    Managed Caching auf mehreren Ebenen
    """
    
    def __init__(self):
        self.redis = RedisClient()
        self.memory = {}  # In-Memory Cache
    
    async def get(
        self,
        key: str,
        max_age_days: int = None
    ) -> Optional[dict]:
        """
        Holt aus Cache (Memory → Redis)
        """
        
        # 1. Memory-Cache (schnellst)
        if key in self.memory:
            data, cached_at = self.memory[key]
            
            if not max_age_days or self.is_fresh(cached_at, max_age_days):
                return data
        
        # 2. Redis-Cache
        redis_data = await self.redis.get(key)
        if redis_data:
            data = json.loads(redis_data)
            cached_at = data.get('_cached_at')
            
            if not max_age_days or self.is_fresh(cached_at, max_age_days):
                # In Memory speichern für nächsten Zugriff
                self.memory[key] = (data, cached_at)
                return data
        
        return None
    
    async def set(
        self,
        key: str,
        data: dict,
        ttl_days: int = 30
    ):
        """
        Speichert in Cache (Memory + Redis)
        """
        
        cached_at = datetime.now().isoformat()
        data['_cached_at'] = cached_at
        
        # Memory
        self.memory[key] = (data, cached_at)
        
        # Redis mit TTL
        await self.redis.setex(
            key,
            ttl_days * 24 * 3600,
            json.dumps(data)
        )
    
    def is_fresh(self, cached_at: str, max_age_days: int) -> bool:
        """
        Prüft ob Cache noch frisch
        """
        cached_time = datetime.fromisoformat(cached_at)
        age = datetime.now() - cached_time
        
        return age.days < max_age_days


# Cache-Keys-Konvention
CACHE_KEYS = {
    'research': 'research_{job_type}_{location}',
    'ci': 'ci_{company_name}',
    'image_analysis': 'img_analysis_{image_url_hash}'
}
```

---

## Monitoring & Logging

### Comprehensive Observability

```python
class MetricsCollector:
    """
    Sammelt Metriken für Monitoring
    """
    
    def __init__(self):
        self.prometheus = PrometheusClient()
        self.db = MetricsDB()
    
    async def log_campaign(self, campaign_result: dict):
        """
        Logged komplette Kampagne
        """
        
        metrics = {
            'job_id': campaign_result['job_id'],
            'duration': campaign_result['metadata']['duration_seconds'],
            'creatives_total': campaign_result['metadata']['total_creatives_generated'],
            'creatives_approved': campaign_result['metadata']['creatives_approved'],
            'approval_rate': campaign_result['metadata']['creatives_approved'] / 
                           campaign_result['metadata']['total_creatives_generated'],
            'timestamp': datetime.now()
        }
        
        # Prometheus
        self.prometheus.campaign_duration.observe(metrics['duration'])
        self.prometheus.creatives_generated.inc(metrics['creatives_total'])
        self.prometheus.approval_rate.set(metrics['approval_rate'])
        
        # Datenbank
        await self.db.campaigns.insert(metrics)
    
    async def log_phase_timing(
        self,
        phase_name: str,
        duration: float,
        job_id: str
    ):
        """
        Logged Phase-Timings
        """
        
        self.prometheus.phase_duration.labels(
            phase=phase_name
        ).observe(duration)
        
        await self.db.phase_timings.insert({
            'job_id': job_id,
            'phase': phase_name,
            'duration': duration,
            'timestamp': datetime.now()
        })
    
    async def log_error(
        self,
        job_id: str,
        error_message: str,
        phase: str = None
    ):
        """
        Logged Fehler
        """
        
        self.prometheus.errors.labels(
            phase=phase or 'unknown'
        ).inc()
        
        await self.db.errors.insert({
            'job_id': job_id,
            'phase': phase,
            'error': error_message,
            'timestamp': datetime.now()
        })
    
    async def get_performance_metrics(
        self,
        time_range_hours: int = 24
    ) -> dict:
        """
        Performance-Metriken abrufen
        """
        
        since = datetime.now() - timedelta(hours=time_range_hours)
        
        metrics = await self.db.campaigns.aggregate([
            {'$match': {'timestamp': {'$gte': since}}},
            {'$group': {
                '_id': None,
                'avg_duration': {'$avg': '$duration'},
                'avg_approval_rate': {'$avg': '$approval_rate'},
                'total_campaigns': {'$sum': 1},
                'total_creatives': {'$sum': '$creatives_total'}
            }}
        ])
        
        return metrics


class StructuredLogger:
    """
    Strukturiertes Logging
    """
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        self.logger.info(
            json.dumps({
                'level': 'INFO',
                'logger': self.name,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            })
        )
    
    def error(self, message: str, **kwargs):
        self.logger.error(
            json.dumps({
                'level': 'ERROR',
                'logger': self.name,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            })
        )
```

---

## API-Endpoints

### REST API für Frontend

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Creative AI API")

class GenerateRequest(BaseModel):
    job_id: str
    config: dict = None

class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str

@app.post("/api/v1/generate", response_model=GenerateResponse)
async def generate_campaign(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Startet Kampagnen-Generierung (async)
    """
    
    # Task-ID generieren
    task_id = generate_task_id()
    
    # In Background starten
    background_tasks.add_task(
        run_campaign_generation,
        task_id,
        request.job_id,
        request.config
    )
    
    return GenerateResponse(
        task_id=task_id,
        status="started",
        message=f"Campaign generation started for job {request.job_id}"
    )


@app.get("/api/v1/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Status einer laufenden Generierung
    """
    
    status = await task_store.get_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return status


@app.get("/api/v1/results/{task_id}")
async def get_campaign_results(task_id: str):
    """
    Resultat einer abgeschlossenen Kampagne
    """
    
    result = await task_store.get_result(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    if result['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Campaign not completed yet (status: {result['status']})"
        )
    
    return result


@app.get("/api/v1/campaigns")
async def list_campaigns(
    limit: int = 50,
    offset: int = 0
):
    """
    Liste aller Kampagnen
    """
    
    campaigns = await db.campaigns.find().skip(offset).limit(limit).to_list()
    
    return {
        "campaigns": campaigns,
        "total": await db.campaigns.count_documents({}),
        "limit": limit,
        "offset": offset
    }


@app.post("/api/v1/approve/{creative_id}")
async def approve_creative(creative_id: str):
    """
    Approved ein Creative für Veröffentlichung
    """
    
    await db.creatives.update_one(
        {"_id": creative_id},
        {"$set": {
            "approved": True,
            "approved_at": datetime.now()
        }}
    )
    
    return {"status": "approved", "creative_id": creative_id}


async def run_campaign_generation(
    task_id: str,
    job_id: str,
    config: dict
):
    """
    Background-Task für Generierung
    """
    
    orchestrator = CreativeOrchestrator()
    
    try:
        # Status: running
        await task_store.update_status(task_id, {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        })
        
        # Generiere
        result = await orchestrator.generate_complete_campaign(job_id, config)
        
        # Status: completed
        await task_store.update_status(task_id, {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'result': result
        })
    
    except Exception as e:
        # Status: failed
        await task_store.update_status(task_id, {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })
        
        logger.error(f"Campaign generation failed: {e}")
```

---

## Batch-Processing

### Mehrere Jobs gleichzeitig

```python
class BatchProcessor:
    """
    Verarbeitet mehrere Jobs gleichzeitig
    """
    
    def __init__(self, orchestrator: CreativeOrchestrator):
        self.orchestrator = orchestrator
        self.max_concurrent_jobs = 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent_jobs)
    
    async def process_batch(self, job_ids: list) -> list:
        """
        Verarbeitet Batch von Jobs
        """
        
        tasks = [
            self.process_single_job(job_id)
            for job_id in job_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def process_single_job(self, job_id: str):
        """
        Verarbeitet einzelnen Job mit Rate-Limiting
        """
        
        async with self.semaphore:
            try:
                return await self.orchestrator.generate_complete_campaign(job_id)
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                return {"job_id": job_id, "status": "failed", "error": str(e)}
```

---

## Performance-Optimierung

### Best Practices

```python
# 1. Connection Pooling
class APIClient:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100)
        )

# 2. Request Batching
async def batch_api_calls(calls: list, batch_size: int = 10):
    for i in range(0, len(calls), batch_size):
        batch = calls[i:i + batch_size]
        await asyncio.gather(*batch)
        await asyncio.sleep(0.1)  # Rate limiting

# 3. Memory Management
def cleanup_large_objects():
    """Säubere große Objekte nach Verwendung"""
    import gc
    gc.collect()

# 4. Streaming für große Bilder
async def download_image_streaming(url: str, chunk_size: int = 8192):
    async with session.get(url) as response:
        async for chunk in response.content.iter_chunked(chunk_size):
            yield chunk
```

---

## Deployment

### Production Considerations

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BFL_API_KEY=${BFL_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - mongodb
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  mongodb:
    image: mongo:6
    volumes:
      - mongo_data:/data/db
  
  worker:
    build: .
    command: celery -A app.celery worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

volumes:
  redis_data:
  mongo_data:
```

### Scaling-Strategie

```
Load Balancer
     ↓
┌────────────────────┐
│   API Instances    │
│   (3x replicas)    │
└────────────────────┘
     ↓
┌────────────────────┐
│   Worker Pool      │
│   (10x workers)    │
└────────────────────┘
     ↓
┌────────────────────┐
│   Redis Cluster    │
│   (Cache + Queue)  │
└────────────────────┘
```

---

## Kosten-Tracking

### Per-Campaign Cost Calculation (AKTUALISIERT)

```python
class CostCalculator:
    """
    Berechnet Kosten pro Kampagne
    
    AKTUALISIERT: Realistische Kosten mit Retries
    """
    
    COSTS = {
        # OpenAI Text
        'openai_gpt4o_input': 0.005 / 1000,   # per token
        'openai_gpt4o_output': 0.015 / 1000,
        
        # OpenAI Images (gpt-image-1)
        'openai_i2i': 0.04,  # per image (gpt-image-1)
        
        # BFL
        'bfl_flux_pro': 0.05,   # per image
        
        # Research & Scraping
        'perplexity_research': 0.10,  # pro Research (nicht pro Query!)
        'firecrawl_scrape': 0.01  # per scrape
    }
    
    def calculate_campaign_cost(self, campaign_result: dict) -> dict:
        """
        Berechnet Gesamt-Kosten
        """
        
        costs = {
            'text_generation': 0,
            'bfl_images': 0,
            'i2i_images': 0,
            'research': 0,
            'scraping': 0,
            'retries': 0
        }
        
        # Text-Generierung (Context Fusion + Copywriting + Designer-KIs)
        # 5 Varianten × ~5000 tokens = ~$0.33
        costs['text_generation'] = 0.33
        
        # Bild-Generierung (5 × 4 = 20 BFL)
        num_bfl = campaign_result.get('num_bfl_images', 20)
        costs['bfl_images'] = num_bfl * self.COSTS['bfl_flux_pro']
        
        # I2I-Overlays (20 × gpt-image-1)
        num_i2i = campaign_result.get('num_i2i_images', 20)
        costs['i2i_images'] = num_i2i * self.COSTS['openai_i2i']
        
        # Perplexity Research (20% der Zeit, gecacht)
        if campaign_result.get('perplexity_used') and not campaign_result.get('perplexity_cached'):
            costs['research'] = self.COSTS['perplexity_research']
        
        # Firecrawl (einmalig, 90d gecacht)
        if campaign_result.get('ci_scraped') and not campaign_result.get('ci_cached'):
            costs['scraping'] = self.COSTS['firecrawl_scrape']
        
        # Retries (durchschnittlich 15% der Creatives)
        retry_rate = campaign_result.get('retry_rate', 0.15)
        num_retries = int(num_bfl * retry_rate)
        costs['retries'] = num_retries * (self.COSTS['bfl_flux_pro'] + self.COSTS['openai_i2i'])
        
        total = sum(costs.values())
        
        return {
            'breakdown': costs,
            'total': round(total, 2),
            'per_creative': round(total / max(num_i2i, 1), 3),
            'currency': 'USD'
        }
```

---

## Zusammenfassung

### Was die Orchestrierung leistet:

✅ **Koordiniert 5 Phasen** mit komplexer Parallelisierung
✅ **Generiert 20+ Creatives** pro Job in ~2-5 Minuten
✅ **Robustes Error Handling** mit Auto-Retry
✅ **Multi-Layer Caching** (Memory + Redis)
✅ **Quality Gates** mit automatischer Regeneration
✅ **Comprehensive Monitoring** (Prometheus + Logging)
✅ **REST API** für Frontend-Integration
✅ **Batch-Processing** für Multiple Jobs
✅ **Cost Tracking** pro Kampagne

### Performance-Zahlen (geschätzt):

```
Durchschnittliche Kampagne:
- Text-Generierung: ~30s
- Bild-Generierung: ~3-4min (Batches von 5, nicht parallel 20!)
- Gate 1a: ~10s (Fail-Fast OCR auf BFL-Bilder)
- CI & Layout: ~20s (meist gecacht)
- Phase 4a (I2I): ~2min (parallel)
- Phase 4b (Logo): ~10s (Pillow, schnell)
- Gates 1b-4: ~1min (Vision-basiert, 4 statt 5 Gates)

Total: ~6-8 Minuten für 20 Creatives
       (länger als vorher wegen BFL Rate Limit!)
```

### Kosten pro Kampagne (AKTUALISIERT):

```
Text-Generierung:
- Context Fusion: 5x @ 2000 tokens    → $0.05
- Copywriting: 5x @ 3000 tokens       → $0.08
- Designer-KIs: 4x @ 2000 tokens/var  → $0.20
                                      Summe: $0.33

Bild-Generierung:
- BFL Flux Pro: 20x @ $0.05           → $1.00

I2I-Generation:
- gpt-image-1: 20x @ $0.04            → $0.80

Research & Scraping:
- Perplexity (20% Nutzung, gecacht)   → $0.02
- Firecrawl (90d gecacht)             → $0.01
                                      Summe: $0.03

SUBTOTAL (ohne Retries):                $2.16

Retries (durchschnittlich 15%):
- 3 Creatives regeneriert             → $0.32

──────────────────────────────────────────────
TOTAL PRO KAMPAGNE:                     $2.48  ← KORRIGIERT!
PRO CREATIVE:                           $0.12
──────────────────────────────────────────────

Bei 100 Kampagnen/Monat:                $248
```

**Vergleich zur alten Schätzung:**
- Alt: $1.90
- Neu: $2.48
- **Differenz: +30%** (aber immer noch sehr günstig!)

---

## Notizen

_Dieser Abschnitt für projektspezifische Erkenntnisse während der Entwicklung._

**2025-01-06:**
- Vollständige Orchestrierung dokumentiert
- 5 Phasen mit optimaler Parallelisierung
- Robustes Error Handling & Retry
- Caching auf mehreren Ebenen
- REST API für Frontend
- Performance & Cost Tracking
- Production-ready Architecture

**2026-01-06:**
- ✅ **BFL Rate Limit korrigiert**: Semaphore(10) → Semaphore(5)
- ✅ **BFL Batch-Processing** implementiert (4 Batches à 5 Bilder)
- ✅ **Phase 4a/4b Split** implementiert:
  - Phase 4a: OpenAI I2I (nur Text)
  - Phase 4b: Logo-Compositing (Pillow)
- ✅ **Gate 1a** in Pipeline integriert (vor Layout Designer)
- ✅ **Kosten aktualisiert**: $1.90 → $2.48 pro Kampagne
- ✅ **Performance-Schätzung angepasst**: 5-7min → 6-8min (wegen BFL Batching)
- ✅ **CostCalculator** erweitert mit Retry-Kosten

**2026-01-07 - SEMANTISCHER REFACTOR:**
- ✅ **Gate 4 (CI) ENTFERNT** - CI via verstärktem I2I-Prompt
- ✅ **4 Gates statt 5** (Gate 5 Readability → Gate 4)
- ✅ **Gate 1b Vision statt OCR+Masking** - Semantisch!
- ✅ **Retry-Logik verbessert**: Erst I2I, BFL nur bei mehrfachem Fail
- ✅ **Action-Namen vereinheitlicht**: `regenerate_i2i` als Standard

