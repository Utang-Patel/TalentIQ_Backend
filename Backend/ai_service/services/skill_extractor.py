import re


def extract_skills_from_text(text, skills):
    """
    Resume text se skills aur unke aliases detect karta hai.
    """

    text_lower = text.lower()

    matched_skills = []

    for skill in skills:

        # Skill name
        terms = [skill.skill_name]

        # Aliases bhi add karo
        if skill.aliases:
            aliases = skill.aliases.split(",")

            for alias in aliases:
                alias = alias.strip()

                if alias:
                    terms.append(alias)

        found_term = None

        # Skill name / aliases search karo
        for term in terms:

            term_lower = term.lower()

            pattern = r'\b' + re.escape(term_lower) + r'\b'

            if re.search(pattern, text_lower):
                found_term = term
                break

        # Skill mil gayi
        if found_term:

            matched_skills.append({
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "matched_term": found_term,
                "confidence_score": 95.0
            })

    return matched_skills