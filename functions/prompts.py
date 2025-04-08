findings = """
Extract key findings from the abstract as bullet points, following these rules:

Formatting:
- Present only substantiated findings
- Skip bullet points entirely if the abstract is purely theoretical or does not present findings
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
- Summaries: Clear, quantified bullet points [Follow rules from first section]
- Note [if no bullets extracted]:
  1. type: state the paper type, e.g.
    - "Workshop announcement"
    - "Conceptual framework"
    - "Design methodology"
    - "Technical specification"
    - "Systematic review"
    - "System and methology improvement"
  2. description: summarize the content of the paper within 1 sentence
  
In addition, extract 1-3 keywords from the abstract:
- Keywords [1-3]: Main topics and themes of the paper

include:
- Domain terms (e.g., "Healthcare", "Education")
- Target outcomes (e.g., "Team Efficiency", "Learning")
- Specific contexts (e.g., "Emergency Response", "K-12")

DO NOT include:
- Generic HCI/AI-related terms (e.g., "Human-AI Interaction", "Human-Computer Interaction", "Artificial Intellegence")
"""