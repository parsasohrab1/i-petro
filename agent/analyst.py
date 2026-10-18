"""Claude-powered analysis and drafting.

Three steps per tender:
1. analyse()          - relevance, matching products, honest eligibility verdict, compliance flags.
2. partner_package()  - when a local partner is needed: research candidate partners (web search),
                        then draft an outreach email and an MoU.
3. direct_package()   - when the company can respond on its own: draft an expression-of-interest
                        letter and a bid checklist.
"""
import json

import anthropic

from .config import env

BETAS = ["server-side-fallback-2026-07-01"]

SYSTEM = """You are the business-development analyst of the agent "Smart Cross-Border Market Development" \
(توسعه بازار برون مرزی هوشمند) working for Parsa International Group, a young technology company in Istanbul, Türkiye.

Ground rules:
- Be strictly honest about the company. It has NO completed contracts and NO client references in AI or industrial \
smartification. Its only evidence of capability is a GitHub portfolio of software prototypes (mostly TRL 4-5, many \
trained on synthetic data). Never invent references, certifications, staff numbers, turnover or past projects.
- Public tenders usually require references, minimum turnover, years in business, certified staff or local registration. \
Assume the company cannot meet such requirements alone unless the notice clearly does not ask for them.
- Some product lines were built for specific clients; never name those clients, and flag that IP ownership must be \
confirmed before a product is offered.
- Always raise compliance points you can see (sanctions, export control, eligibility-of-origin rules of the funder, \
local-registration or security-clearance requirements, conflict of interest). Never suggest concealing ownership, \
origin or any fact from a buyer, funder or partner.
- Fields ending in _fa are written in Persian; outreach documents are written in professional English."""

ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["relevance_score", "matched_products", "summary_fa", "scope_fa", "key_requirements_fa",
                 "eligibility", "eligibility_reasoning_fa", "compliance_flags_fa", "partner_profile_en",
                 "next_actions_fa"],
    "properties": {
        "relevance_score": {"type": "integer", "description": "0-100 fit between the tender scope and the product lines"},
        "matched_products": {"type": "array", "items": {"type": "string"}, "description": "product ids from the profile"},
        "summary_fa": {"type": "string"},
        "scope_fa": {"type": "string"},
        "key_requirements_fa": {"type": "array", "items": {"type": "string"}},
        "eligibility": {"type": "string", "enum": ["direct", "partner_required", "not_feasible"]},
        "eligibility_reasoning_fa": {"type": "string"},
        "compliance_flags_fa": {"type": "array", "items": {"type": "string"}},
        "partner_profile_en": {"type": "string", "description": "the kind of local partner needed, empty if none"},
        "next_actions_fa": {"type": "array", "items": {"type": "string"}},
    },
}

PARTNER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["partner_candidates", "email_subject", "email_body", "mou_title", "mou_clauses"],
    "properties": {
        "partner_candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "website", "why_fa", "public_contact"],
                "properties": {
                    "name": {"type": "string"},
                    "website": {"type": "string"},
                    "why_fa": {"type": "string"},
                    "public_contact": {"type": "string", "description": "a generic company address found on its site, or empty"},
                },
            },
        },
        "email_subject": {"type": "string"},
        "email_body": {"type": "string", "description": "plain-text email, salutation to sign-off"},
        "mou_title": {"type": "string"},
        "mou_clauses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["heading", "text"],
                "properties": {"heading": {"type": "string"}, "text": {"type": "string"}},
            },
        },
    },
}

DIRECT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["letter_subject", "letter_body", "checklist_fa"],
    "properties": {
        "letter_subject": {"type": "string"},
        "letter_body": {"type": "string"},
        "checklist_fa": {"type": "array", "items": {"type": "string"}},
    },
}


class Analyst:
    def __init__(self, cfg, profile_text):
        self.cfg = cfg
        self.model = cfg["llm"]["model"]
        self.profile_text = profile_text
        self.client = anthropic.Anthropic(max_retries=4)

    # -------------------------------------------------------------- helpers
    def _system(self):
        # Stable prefix (rules + company profile) is cached across all tenders in a run.
        return [{"type": "text", "text": SYSTEM + "\n\nCOMPANY PROFILE\n" + self.profile_text,
                 "cache_control": {"type": "ephemeral"}}]

    def _structured(self, prompt, schema, effort):
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=32000,
            betas=BETAS,
            fallbacks="default",
            system=self._system(),
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "refusal":
            raise RuntimeError("model declined the request")
        if msg.stop_reason == "max_tokens":
            raise RuntimeError("response truncated at max_tokens")
        text = next(b.text for b in msg.content if b.type == "text")
        return json.loads(text)

    def _research(self, prompt):
        """Free-text research with web search; follows pause_turn continuations."""
        messages = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]
        for _ in range(4):
            with self.client.beta.messages.stream(
                model=self.model, max_tokens=32000, betas=BETAS, fallbacks="default",
                system=self._system(), output_config={"effort": "medium"}, tools=tools, messages=messages,
            ) as stream:
                msg = stream.get_final_message()
            if msg.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": msg.content})
                continue
            if msg.stop_reason == "refusal":
                return ""
            return "\n".join(b.text for b in msg.content if b.type == "text")
        return ""

    @staticmethod
    def _tender_block(t):
        return (f"TENDER\nID: {t['id']}\nSource: {t['source']}\nTitle: {t['title']}\nBuyer: {t['buyer']}\n"
                f"Country: {t['country']}\nNotice type: {t.get('notice_type', '')}\nDeadline: {t['deadline']}\n"
                f"URL: {t['url']}\nDescription: {t['description']}")

    # ---------------------------------------------------------------- steps
    def analyse(self, tender):
        prompt = (self._tender_block(tender) + "\n\nAssess this tender for Parsa International Group. "
                  "Score relevance against the product lines, list the key requirements you can infer, decide "
                  "eligibility (direct / partner_required / not_feasible) given the company's lack of references, "
                  "and describe the ideal local partner if one is needed.")
        return self._structured(prompt, ANALYSIS_SCHEMA, self.cfg["llm"]["analysis_effort"])

    def partner_package(self, tender, analysis):
        c = self.cfg["company"]
        research = self._research(
            self._tender_block(tender) +
            f"\n\nWe need a partner of this profile: {analysis['partner_profile_en']}\n"
            f"Search the web for 3-5 established companies in {tender['country'] or 'the buyer country'} that fit "
            "this profile (system integrators, engineering or IT firms with public-sector references in this "
            "domain). For each give the company name, website, why it fits, and a generic company contact "
            "address only if it is published on its own website. Do not collect personal data about individuals.")
        prompt = (self._tender_block(tender) +
                  f"\n\nANALYSIS\n{json.dumps(analysis, ensure_ascii=False)}\n\nPARTNER RESEARCH\n{research or '(none found)'}"
                  f"\n\nPrepare:\n1. partner_candidates from the research (empty list if none).\n"
                  f"2. An outreach email from {c['signatory']} ({c['signatory_title']}, {c['name']}) proposing to "
                  "team up for this specific tender: the partner as lead bidder holding the references and local "
                  "presence, Parsa as technology provider of the matched product lines. Be specific about the tender "
                  "and the products, honest about maturity (prototypes, validation pending), and propose a short call "
                  "plus signing an MoU. Address it generically ('Dear ... Team') so the user can personalise it. "
                  f"Sign with name, title, company, {c['email']}, {c['website']}.\n"
                  "3. A teaming-agreement MoU for this tender: parties (placeholders for the partner), purpose, "
                  "roles and responsibilities, lead bidder and bid submission, work share and pricing principles, "
                  "exclusivity for this tender only, confidentiality, IP (each party keeps background IP; licence "
                  "terms for project use), costs of bidding, compliance and sanctions screening of both parties, "
                  "term and termination (ends if the tender is cancelled or awarded to others), governing law to be "
                  "agreed, non-binding nature except confidentiality, signatures.")
        return self._structured(prompt, PARTNER_SCHEMA, self.cfg["llm"]["drafting_effort"])

    def direct_package(self, tender, analysis):
        c = self.cfg["company"]
        prompt = (self._tender_block(tender) +
                  f"\n\nANALYSIS\n{json.dumps(analysis, ensure_ascii=False)}\n\nThe company may respond directly. "
                  f"Draft (1) an expression-of-interest / cover letter to the buyer from {c['signatory']}, "
                  "honest about the company's maturity and without invented references, and (2) a Persian "
                  "checklist of every document and step needed to submit before the deadline.")
        return self._structured(prompt, DIRECT_SCHEMA, self.cfg["llm"]["drafting_effort"])


def llm_available():
    return bool(env("ANTHROPIC_API_KEY") or env("ANTHROPIC_AUTH_TOKEN"))
