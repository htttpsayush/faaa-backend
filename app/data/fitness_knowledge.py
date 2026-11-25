"""Curated, lightweight fitness & nutrition knowledge base for Hybrid RAG retrieval.

Kept as pure Python data (zero vector DB / embedding model RAM overhead)
covering hypertrophy, fat loss, Indian high-protein veg/non-veg meal swaps,
hydration, sleep recovery, and injury/rehab safety rules.
"""

from typing import List, Dict

FITNESS_KNOWLEDGE_CHUNKS: List[Dict[str, object]] = [
    {
        "id": "hypertrophy_principles",
        "topic": "Muscle Hypertrophy",
        "tags": [
            "muscle", "hypertrophy", "bulk", "strength", "gym", "volume",
            "sets", "reps", "progressive", "overload", "workout", "plan",
        ],
        "content": (
            "Muscle hypertrophy requires mechanical tension and progressive overload: "
            "aim for 10-20 hard working sets per muscle group per week, mostly in the "
            "6-15 rep range taken 1-3 reps shy of failure (RPE 7-9). Track total weekly "
            "volume (kg) and increase weight or reps gradually across sessions. Rest 90-150s "
            "on compound lifts and 60-90s on isolation exercises."
        ),
    },
    {
        "id": "fat_loss_fundamentals",
        "topic": "Fat Loss & Body Recomposition",
        "tags": [
            "fat", "loss", "cut", "lean", "deficit", "calories", "weight",
            "cardio", "steps", "macro", "shortfall", "diet",
        ],
        "content": (
            "Sustainable fat loss comes from a moderate 300-500 kcal daily caloric deficit "
            "paired with high protein (1.6-2.2 g/kg bodyweight) to preserve lean muscle. "
            "Prioritize resistance training 3-5x/week plus high daily NEAT (8,000-10,000 steps) "
            "rather than crash dieting. Avoid cutting calories too aggressively, which spikes "
            "fatigue and causes muscle loss."
        ),
    },
    {
        "id": "indian_veg_protein_swaps",
        "topic": "Indian Vegetarian High-Protein Swaps",
        "tags": [
            "veg", "vegetarian", "indian", "protein", "paneer", "soya", "dal",
            "curd", "macro", "meal", "swap", "gap", "shortfall", "food",
        ],
        "content": (
            "Top Indian vegetarian high-protein swaps to close macro gaps without blowing "
            "fat/calorie budgets: swap regular paneer for low-fat paneer (20-25g protein/100g) "
            "or tofu; add boiled soya chunks (52g protein/100g dry) to pulao or bhurji; "
            "use hung curd/Greek yogurt (10g protein/100g) instead of heavy cream raita; "
            "combine moong dal chilla with paneer/sprouts stuffing or roasted chana + whey "
            "shake with oats for easy 25-35g protein meals."
        ),
    },
    {
        "id": "indian_nonveg_protein_swaps",
        "topic": "Indian Non-Vegetarian High-Protein Swaps",
        "tags": [
            "non_veg", "non-veg", "chicken", "egg", "fish", "indian", "protein",
            "macro", "meal", "swap", "gap", "shortfall", "food",
        ],
        "content": (
            "Top Indian non-vegetarian high-protein swaps: choose skinless chicken breast "
            "or dry tandoori/tikka cuts (31g protein/100g cooked) over butter/malai gravies; "
            "pair 2 whole eggs with 4-5 egg whites for a lean 28g protein omelette; use grilled "
            "rohu, pomfret, or canned tuna in water; swap mutton curry for lean chicken keema "
            "with minimal oil to hit protein targets cleanly."
        ),
    },
    {
        "id": "hydration_electrolytes",
        "topic": "Hydration & Electrolytes",
        "tags": [
            "hydration", "water", "electrolytes", "sweat", "cramp", "endurance",
            "speed", "recovery", "performance", "fatigue",
        ],
        "content": (
            "Baseline hydration target is 35-45 ml of water per kg of bodyweight daily "
            "(~2.5-3.5L for most athletes), plus 500-750 ml per hour of intense training. "
            "Even 2% dehydration drops strength, sprint speed, and focus. For heavy sweat "
            "sessions, replenish sodium and potassium with a pinch of salt + lemon water "
            "or coconut water."
        ),
    },
    {
        "id": "sleep_recovery_discipline",
        "topic": "Sleep & Recovery Discipline",
        "tags": [
            "sleep", "recovery", "rest", "fatigue", "soreness", "discipline",
            "consistency", "rate", "week", "hormones", "cortisol", "habit",
        ],
        "content": (
            "Champions are built during recovery: target 7.5-9 hours of consistent sleep "
            "with a fixed wake/sleep window. Poor sleep lowers muscle protein synthesis, "
            "elevates cortisol, and spikes cravings. Schedule 1-2 active recovery/rest days "
            "per week and take a lighter deload week every 6-8 weeks of hard training."
        ),
    },
    {
        "id": "injury_rehab_safety",
        "topic": "Injury & Rehab Safety Rules",
        "tags": [
            "injury", "rehab", "pain", "sore", "joint", "knee", "shoulder",
            "back", "mobility", "safety", "doctor", "physio",
        ],
        "content": (
            "Rehab & injury safety: NEVER push through sharp, joint-locking, or radiating "
            "pain. If pain is >= 7/10, stop training that area immediately and consult a "
            "licensed physician or physiotherapist. For mild stiffness (< 4/10), stick to "
            "gentle pain-free range of motion, slow controlled tempo, and isometric holds. "
            "Guidance is educational only, not medical diagnosis."
        ),
    },
]
