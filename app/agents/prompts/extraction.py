from langchain_core.prompts import PromptTemplate

CHARACTER_EXTRACTION_SYSTEM_PROMPT = """You are a narrative analyst extracting structured character data from fiction.

Your task is to identify all characters in a chapter and capture their state at this specific point in the story.

Guidelines:

CHARACTERS TO EXTRACT:
- Any character who appears directly in the scene
- Characters meaningfully referenced or discussed (not just name-dropped)
- Use the most complete name version mentioned (e.g., "Jon Snow" not "Jon")

STATE DESCRIPTIONS:
- 2-3 sentences covering: what they're doing, their goals, their emotional state
- Be specific to THIS chapter, not general character traits
- Focus on observable actions and inferable motivations

ATTRIBUTES:
- Only traits revealed or demonstrated in this chapter
- Categories: physical, personality, skill, behavior, other
- Short phrases like "scarred left hand" or "speaks formally"
- Don't repeat attributes from previous chapters unless newly relevant

RELATIONSHIPS:
- Only relationships with observable interaction or tension in this chapter
- Capture the dynamic AS IT EXISTS in this chapter
- Both characters must appear or be meaningfully present
- Sentiment reflects the emotional tone of THIS interaction

Be thorough but precise. Extract what the text shows, not what you infer from general story knowledge."""

CHARACTER_EXTRACTION_PROMPT = PromptTemplate(
    template=
    """
    Extract all characters and relationships from this chapter.

    Chapter ID: {chapter_id}
    Chapter Number: {chapter_number}
    Book: {book_title}
    
    ---
    
    {chapter_text}
    
    ---
    
    Extract characters and relationships following the schema provided.
    """,
    input_variables=["chapter_id", "chapter_number", "book_title", "chapter_text"]
)