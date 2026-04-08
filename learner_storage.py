import json


SCHEMA_VERSION = 1
DEFAULT_USERNAME = "User"
DEFAULT_AVATAR_ID = "cat_smile"
DEFAULT_AVATAR_BG_ID = "peach"
VALID_AVATAR_IDS = {
    "cat_smile",
    "cat_grin",
    "cat_joy",
    "cat_heart",
    "cat_wry",
    "cat_kiss",
    "cat_scream",
    "cat_cry",
    "cat_pout",
}
VALID_AVATAR_BG_IDS = {
    "peach",
    "butter",
    "mint",
    "sky",
    "lavender",
    "blush",
}


def progress_storage_key(quiz_id: str) -> str:
    return f"quizurself_learner_progress_{quiz_id}_v1"


def session_storage_key(quiz_id: str) -> str:
    return f"quizurself_learner_session_{quiz_id}_v1"


def create_empty_progress(quiz_id: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "quiz_id": quiz_id,
        "username": DEFAULT_USERNAME,
        "avatar_id": DEFAULT_AVATAR_ID,
        "avatar_bg_id": DEFAULT_AVATAR_BG_ID,
        "exported_at": "",
        "user_grit": 0.0,
        "user_grit_updated_at": 0,
        "questions": {},
    }


def blank_question_state() -> dict:
    return {
        "attempts": 0,
        "correct_attempts": 0,
        "confidence_history": [],
        "last_seen_at": 0,
        "last_answer_ms": 0,
        "knowledge": 0.0,
        "meta_learning": 0.0,
        "mastery": 0.0,
        "stability": 0.15,
        "difficulty": 0.5,
        "due_at": 0,
        "consecutive_correct": 0,
        "consecutive_wrong": 0,
        "last_result_correct": False,
        "updated_at": 0,
    }


def normalize_question_state(payload: dict) -> dict:
    state = blank_question_state()
    if not isinstance(payload, dict):
        return state

    state["attempts"] = max(0, int(payload.get("attempts", 0) or 0))
    state["correct_attempts"] = max(0, int(payload.get("correct_attempts", 0) or 0))
    history = payload.get("confidence_history", [])
    if isinstance(history, list):
        state["confidence_history"] = [max(0, min(3, int(value))) for value in history[:50]]
    state["last_seen_at"] = max(0, int(payload.get("last_seen_at", 0) or 0))
    state["last_answer_ms"] = max(0, int(payload.get("last_answer_ms", 0) or 0))
    state["knowledge"] = clamp(float(payload.get("knowledge", 0.0) or 0.0))
    state["meta_learning"] = clamp(float(payload.get("meta_learning", 0.0) or 0.0))
    state["mastery"] = clamp(float(payload.get("mastery", 0.0) or 0.0))
    state["stability"] = clamp(float(payload.get("stability", 0.15) or 0.15), 0.05, 5.0)
    state["difficulty"] = clamp(float(payload.get("difficulty", 0.5) or 0.5))
    state["due_at"] = max(0, int(payload.get("due_at", 0) or 0))
    state["consecutive_correct"] = max(0, int(payload.get("consecutive_correct", 0) or 0))
    state["consecutive_wrong"] = max(0, int(payload.get("consecutive_wrong", 0) or 0))
    state["last_result_correct"] = bool(payload.get("last_result_correct", False))
    state["updated_at"] = max(0, int(payload.get("updated_at", state["last_seen_at"]) or 0))
    return state


def normalize_progress(payload: dict, quiz_id: str, valid_question_ids: set[int]) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Progress JSON must be an object.")

    if int(payload.get("schema_version", 0) or 0) != SCHEMA_VERSION:
        raise ValueError("Unsupported learner progress schema version.")

    if str(payload.get("quiz_id", "")) != quiz_id:
        raise ValueError("This learner progress file is for a different quiz.")

    questions = payload.get("questions", {})
    if not isinstance(questions, dict):
        raise ValueError("Learner progress questions must be an object.")

    normalized = create_empty_progress(quiz_id)
    normalized["username"] = normalize_username(payload.get("username", DEFAULT_USERNAME))
    normalized["avatar_id"] = normalize_avatar_id(payload.get("avatar_id", DEFAULT_AVATAR_ID))
    normalized["avatar_bg_id"] = normalize_avatar_bg_id(payload.get("avatar_bg_id", DEFAULT_AVATAR_BG_ID))
    normalized["exported_at"] = str(payload.get("exported_at", "") or "")
    normalized["user_grit"] = max(0.0, float(payload.get("user_grit", 0.0) or 0.0))
    normalized["user_grit_updated_at"] = max(0, int(payload.get("user_grit_updated_at", 0) or 0))

    legacy_grit_values: list[float] = []
    legacy_grit_timestamps: list[int] = []

    for raw_question_id, raw_state in questions.items():
        try:
            question_id = int(raw_question_id)
        except Exception:
            continue
        if question_id not in valid_question_ids:
            continue
        normalized_state = normalize_question_state(raw_state)
        normalized["questions"][str(question_id)] = normalized_state
        if isinstance(raw_state, dict):
            legacy_grit = max(0.0, float(raw_state.get("grit", 0.0) or 0.0))
            if legacy_grit > 0.0:
                legacy_grit_values.append(legacy_grit)
                legacy_grit_timestamps.append(
                    max(0, int(raw_state.get("updated_at", normalized_state["updated_at"]) or 0))
                )

    if normalized["user_grit_updated_at"] <= 0 and legacy_grit_values:
        normalized["user_grit"] = max(legacy_grit_values)
        normalized["user_grit_updated_at"] = max(legacy_grit_timestamps) if legacy_grit_timestamps else 0

    return normalized


def load_progress(window, quiz_id: str, valid_question_ids: set[int]) -> dict:
    raw = window.localStorage.getItem(progress_storage_key(quiz_id))
    if not raw:
        return create_empty_progress(quiz_id)
    try:
        payload = json.loads(raw)
        return normalize_progress(payload, quiz_id, valid_question_ids)
    except Exception:
        return create_empty_progress(quiz_id)


def save_progress(window, progress: dict) -> None:
    window.localStorage.setItem(
        progress_storage_key(str(progress.get("quiz_id", ""))),
        json.dumps(progress),
    )


def clear_progress(window, quiz_id: str) -> None:
    window.localStorage.removeItem(progress_storage_key(quiz_id))


def load_session(window, quiz_id: str) -> dict | None:
    raw = window.localStorage.getItem(session_storage_key(quiz_id))
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def save_session(window, quiz_id: str, session_payload: dict) -> None:
    window.localStorage.setItem(session_storage_key(quiz_id), json.dumps(session_payload))


def clear_session(window, quiz_id: str) -> None:
    window.localStorage.removeItem(session_storage_key(quiz_id))


def export_payload(progress: dict, exported_at: str) -> dict:
    payload = json.loads(json.dumps(progress))
    payload["username"] = normalize_username(payload.get("username", DEFAULT_USERNAME))
    payload["avatar_id"] = normalize_avatar_id(payload.get("avatar_id", DEFAULT_AVATAR_ID))
    payload["avatar_bg_id"] = normalize_avatar_bg_id(payload.get("avatar_bg_id", DEFAULT_AVATAR_BG_ID))
    payload["exported_at"] = exported_at
    return payload


def normalize_username(value) -> str:
    if not isinstance(value, str):
        return DEFAULT_USERNAME
    username = " ".join(value.replace("\uFFFD", " ").split()).strip()
    if not username:
        return DEFAULT_USERNAME
    return username[:40]


def normalize_avatar_id(value) -> str:
    if not isinstance(value, str):
        return DEFAULT_AVATAR_ID
    avatar_id = value.strip()
    if avatar_id not in VALID_AVATAR_IDS:
        return DEFAULT_AVATAR_ID
    return avatar_id


def normalize_avatar_bg_id(value) -> str:
    if not isinstance(value, str):
        return DEFAULT_AVATAR_BG_ID
    avatar_bg_id = value.strip()
    if avatar_bg_id not in VALID_AVATAR_BG_IDS:
        return DEFAULT_AVATAR_BG_ID
    return avatar_bg_id


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))
