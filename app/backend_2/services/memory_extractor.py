MEMORY_KEYWORDS = [
    "tôi thích",
    "tôi muốn",
    "mục tiêu",
    "ielts",
    "gpa",
    "đam mê",
    "tôi đang học",
    "tôi quan tâm",
]


class MemoryExtractor:

    @staticmethod
    def should_store(text: str) -> bool:
        text = text.lower()

        return any(
            keyword in text
            for keyword in MEMORY_KEYWORDS
        )

    @staticmethod
    def detect_type(text: str) -> str:

        text = text.lower()

        if "ielts" in text or "gpa" in text:
            return "profile"

        if "thích" in text or "quan tâm" in text:
            return "preference"

        if "mục tiêu" in text:
            return "goal"

        return "general"