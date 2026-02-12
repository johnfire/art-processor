"""
AI prompt templates for generating titles and descriptions.
Based on gallery owner and collector perspectives.
"""

TITLE_GENERATION_PROMPT = """You are an experienced art gallery owner and curator. Analyze this painting image and generate 10 diverse, compelling titles.

Requirements:
1. Generate exactly 10 title options
2. Each title should be unique in style:
   - One poetic/evocative title
   - One descriptive/literal title
   - One location-based title (if applicable)
   - One emotional/mood-based title
   - One abstract/conceptual title
   - One quantum physics/uncertainty-inspired title (e.g., "Superposition at Dawn", "Entangled Horizons")
   - One mysterious/enigmatic title (e.g., "The Thirteenth Hour", "Whispers in the Void")
   - One fringe science/speculative title (e.g., "Morphic Resonance", "The Akashic Field")
   - One consciousness/metaphysical title (e.g., "The Observer Effect", "Dreamtime Coordinates")
   - One esoteric/alchemical title (e.g., "The Philosopher's Garden", "Transmutation in Blue")

3. Titles should:
   - Be 2-6 words long
   - Be suitable for a gallery setting
   - Capture the essence of the work
   - Appeal to collectors who appreciate both traditional and unconventional perspectives
   - Avoid clichés
   - Balance accessibility with intrigue

4. Consider the artist's style: influenced by Pre-Raphaelite, British watercolourists, Japanese prints, Renaissance art

Return ONLY a JSON array of 10 title strings, nothing else.
Example format: ["Title One", "Title Two", "Title Three", "Title Four", "Title Five", "Title Six", "Title Seven", "Title Eight", "Title Nine", "Title Ten"]
"""

DESCRIPTION_GENERATION_PROMPT = """You are an experienced art gallery owner writing a description for a collector/buyer.

Painting Title: {title}
Medium: {medium}
Dimensions: {dimensions}
Category: {category}
{user_notes_section}
Write a compelling gallery description that includes:

1. VISUAL ANALYSIS (2-3 sentences):
   - Composition and structure
   - Color palette and technique
   - Key visual elements
   - Incorporate any relevant information from the Artist's Notes if provided

2. EMOTIONAL IMPACT (1-2 sentences):
   - Mood and atmosphere
   - What feelings does it evoke?
   - Consider the artist's perspective from their notes if available

3. TECHNICAL NOTES (1-2 sentences):
   - Medium-specific observations
   - Artistic technique or style influences
   - Connections to artist's background (Pre-Raphaelite, Japanese prints, Renaissance influences)
   - Weave in any technical details from the Artist's Notes

Keep the tone:
- Professional but accessible
- Focused on the collector's experience
- Between 100-150 words
- No marketing hype, just honest appreciation

Write the description in paragraph form, no bullet points or numbered lists.
"""

CATEGORY_DETECTION_PROMPT = """Based on this image, which category best fits this artwork?

Available categories: {categories}

Return ONLY the category name, nothing else.
"""
