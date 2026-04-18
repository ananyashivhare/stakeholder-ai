import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Each stakeholder has a specific persona and communication style
STAKEHOLDERS = {
    "CEO / CXO": {
        "persona": "a Fortune 500 CEO who reads 200 emails a day",
        "style": "ultra-concise (max 80 words), strategic framing, focus on business risk and impact, no jargon, strong opening line, ends with one clear ask or decision needed",
        "icon": "👔"
    },
    "Technical Lead": {
        "persona": "a senior software architect who wants technical facts",
        "style": "detailed and specific, include technical context, mention dependencies, suggest technical actions, use bullet points, no business fluff",
        "icon": "💻"
    },
    "Client / External Stakeholder": {
        "persona": "a client who is paying for results and needs reassurance",
        "style": "warm and professional, focus on outcomes not problems, emphasise what is being handled, avoid internal jargon, end on a confident note",
        "icon": "🤝"
    },
    "Finance / CFO": {
        "persona": "a CFO who only cares about budget, cost, and timeline",
        "style": "lead with numbers and dates, quantify any impact (cost/time), be direct about budget implications, propose mitigation with cost estimate if possible",
        "icon": "💰"
    },
    "Compliance / Regulator": {
        "persona": "a regulatory body representative reviewing formal documentation",
        "style": "formal letter format, reference compliance standards where relevant, document-grade language, include date, from/to fields, avoid casual tone",
        "icon": "📋"
    },
}

def personalise_message(original_update, project_name, selected_stakeholders):
    """
    Takes one project update and generates personalised versions
    for each selected stakeholder type.
    Returns a dict: {stakeholder_name: personalised_message}
    """
    results = {}

    for stakeholder in selected_stakeholders:
        if stakeholder not in STAKEHOLDERS:
            continue

        persona = STAKEHOLDERS[stakeholder]['persona']
        style = STAKEHOLDERS[stakeholder]['style']

        prompt = f'''You are an expert project management communication specialist.
Your job is to rewrite a project update for a SPECIFIC audience.

PROJECT NAME: {project_name}
AUDIENCE: {stakeholder} — imagine you are writing to {persona}
COMMUNICATION STYLE: {style}

ORIGINAL UPDATE:
{original_update}

IMPORTANT RULES:
- Preserve all factual information from the original update
- Do NOT add facts that were not in the original
- Write ONLY the message itself — no meta-commentary
- Start directly with the message content
'''

        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=600,
            messages=[{'role': 'user', 'content': prompt}]
        )

        results[stakeholder] = {
            'message': response.content[0].text,
            'icon': STAKEHOLDERS[stakeholder]['icon']
        }

    return results
if __name__ == '__main__':
    test_update = '''Sprint 4 is delayed by 3 days due to an unexpected API
    dependency issue with the payment gateway integration.
    The team identified the root cause and has a fix in progress.
    New go-live estimate: Nov 18. Budget impact: approximately INR 80,000
    in additional developer hours.'''

    results = personalise_message(test_update, 'PaymentPro Project', ['CEO / CXO', 'Technical Lead'])
    for stakeholder, data in results.items():
        print(f'\n=== {data["icon"]} {stakeholder} ===')
        print(data['message'])
