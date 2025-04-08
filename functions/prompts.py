findings = """Extract key findings from the abstract as bullet points, following these rules:
Formatting:
- Present only substantiated findings
- Skip bullet points entirely if the abstract is purely theoretical or does not present findings (in this case, identify the paper type as described in the "Output Format" section below)
- Limit to only the most important findings (typically 0-3 bullets)

Each bullet must:
- State a complete, specific conclusion (e.g., "AI chatbots foster creative collaboration by enabling anonymous idea sharing")
- Be independently understandable without context
- Use concise, precise, simple language
- Focus solely on verified results and findings
- Include metrics when available, but not required
- Include ONLY findings where AI is directly involved in the result
- Describes an AI-related element, explicitly name it as such (e.g. "Design guidelines" → "AI design guidelines", "Explanations" → "AI explanations", "The system's outputs..." → "The AI system's outputs..."); if encountering a non-well-known or product-specific name (e.g. "NeuroSynthVision Pro" or "QuickScribe Assistant"), generalize it to the broader AI concept it represents (e.g. "AI visual synthesis system" or "AI writing assistant").
- Express each finding in Subject-Predicate-Object (SPO) format where possible

Do NOT include:
- Research methodology or process descriptions
- References to "this paper" or "this study"
- Vague comparisons without explanation
- Framework descriptions or conceptual models
- Hypotheses or future work

Sample bullets:
❌ "The system showed improved performance over baseline"
✅ "Virtual reality environments enable deeper emotional engagement in therapy sessions"
✅ "AI-assisted writing tools reduce cognitive load by managing document structure"

Output Format:
- Summaries: Clear, quantified bullet points [Follow rules from the first section]
- Note [if no bullets extracted]:
  1. type: state the paper type, e.g.
    - "Workshop announcement"
    - "Conceptual framework"
    - "Design methodology"
    - "Technical specification"
    - "Systematic review"
    - "System and methodology improvement"
  2. description: summarize the content of the paper within 1 sentence
  
In addition, extract 1-3 keywords from the abstract:
- Keywords [1-3]: Main topics and themes of the paper
include:
- Domain terms (e.g., "Healthcare", "Education")
- Target outcomes (e.g., "Team Efficiency", "Learning")
- Specific contexts (e.g., "Emergency Response", "K-12")
DO NOT include:
- Generic HCI/AI-related terms (e.g., "Human-AI Interaction", "Human-Computer Interaction", "Artificial Intelligence")
"""

triplets = """# Convert research statements about human-AI interaction into structured relationships

Convert research statements into structured triplets using the format:
[cause, relationship, effect] where cause and effect are structured Subject objects.

## Subject Structure
Each Subject has three components:
- *type*: One of only "human", "ai", or "co" (concepts/objects)
- *subtype*: Broad taxonomical category (e.g., "student", "generative")
  - Should be included whenever possible (only omit for very general concepts)
  - Keep subtypes broad enough to be reusable across multiple instances
  - Avoid overly specific subtypes that can't serve as taxonomical categories
  - Use general model types (e.g., "llm", "transformer") not project-specific names
  - Exception: Widely-known models may use their common names (e.g., "chatgpt", "google")

### Subject Categories
Human: Individual actors (e.g., human with subtype "student" or "clinician")
AI: AI systems/components (e.g., ai with subtype "generative" or "chatbot")
CO: Concepts/Objects (e.g., co with subtype "project", "justice", or "interaction")


### Feature Guidelines
One word when possible
Specific over general terms
Use "#" prefix for perception features (e.g., "#trust")
Use colon for nested features (e.g., "creativity:writing")


## Relationship Types
INCREASES/DECREASES

   - For direct impact on measurable attributes
   - Example: AI assistance INCREASES human productivity

INFLUENCES 

   - For complex/indirect effects on behavior/perception
   - Example: AI embodiment INFLUENCES human trust perception

## Examples

Input: "Interactive Machine Learning interfaces enhance artists' creativity in writing by integrating user feedback"

Output:
{
  "cause": {
    "type": "ai",
    "subtype": "interactive",
    "feature": "interface"
  },
  "relationship": "INCREASES",
  "effect": {
    "type": "human",
    "subtype": "artist",
    "feature": "creativity:writing"
  }
}

Input: "Engagement mechanisms improve users' positive perceptions of the robot"

Output:
{
  "cause": {
    "type": "ai",
    "subtype": "",
    "feature": "engagement"
  },
  "relationship": "INCREASES",
  "effect": {
    "type": "human",
    "subtype": "",
    "feature": "#robot"
  }
}

Input: "LLM-based tutoring systems significantly improve learning outcomes for medical students"

Output:
{
  "cause": {
    "type": "ai",
    "subtype": "llm",
    "feature": "tutoring"
  },
  "relationship": "INCREASES",
  "effect": {
    "type": "human",
    "subtype": "student:medical",
    "feature": "learning"
  }
}

Input: "ChatGPT's explanation capability reduces the frequency of user misconceptions about complex topics"

Output:
{
  "cause": {
    "type": "ai",
    "subtype": "chatgpt",
    "feature": "explanation"
  },
  "relationship": "DECREASES",
  "effect": {
    "type": "human",
    "subtype": "user",
    "feature": "misconception:complex"
  }
}

Input: "Collaborative projects between domain experts and generative AI tools lead to more novel solutions"

Output:
{
  "cause": {
    "type": "co",
    "subtype": "collaboration",
    "feature": "expert:ai"
  },
  "relationship": "INCREASES",
  "effect": {
    "type": "co",
    "subtype": "solution",
    "feature": "novelty"
  }
}

## Rules
Focus on primary causal relationship
Use specific terms over general ones

   - ❌ "system features" -> ✅ "explanation interface"
Standardize subjects

   - No redundant terms (e.g., "generative AI" -> type="ai", subtype="generative")
   - Always use lowercase for all fields
   - Prefer using both type AND subtype when possible (only omit subtype for very generalized concepts)
   - Keep subtypes broad and taxonomical rather than overly specific
Remove numerical metrics

   - ❌ "AI performance by 27%" -> ✅ feature="performance"

## Feature Special Cases
Perception (#)

   - Use # prefix for beliefs/perspectives/ideas
   - Example: "perception of trust" -> "#trust"
Nested Features

   - Use colon 🙂) for nested features
   - Use fewest levels possible
   - Example: "reliance on AI" -> "reliance:ai", "misconception about AI" -> "misconception:ai"

## Type and Subtype Rules
For Subject.type, ONLY use "human", "ai", or "co"
Empty string ("") for subtype is valid when no specific subtype applies
Always parse nested subjects correctly:

   - "human:student" → type="human", subtype="student"
   - "ai:generative" → type="ai", subtype="generative"
"""