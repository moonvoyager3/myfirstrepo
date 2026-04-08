from learner_scheduler import MASTERY_THRESHOLD, READY_THRESHOLD, question_state


def scope_label(scope_name: str, all_label: str = "all Knowledge Areas") -> str:
    return all_label if scope_name == "__all__" else scope_name


def area_progress_rows(
    knowledge_areas: list[str],
    question_ids_by_area: dict[str, list[int]],
    progress: dict,
) -> list[dict]:
    rows: list[dict] = []
    for area in knowledge_areas:
        rows.append(progress_for_scope(area, question_ids_by_area.get(area, []), progress))
    return rows


def progress_for_scope(scope_name: str, question_ids: list[int], progress: dict) -> dict:
    total = len(question_ids)
    mastered = 0
    ready = 0
    due_later = 0
    engaged = 0
    overall_mastery_sum = 0.0
    engaged_mastery_sum = 0.0

    for question_id in question_ids:
        state = question_state(progress, question_id)
        mastery = float(state.get("mastery", 0.0) or 0.0)
        attempts = int(state.get("attempts", 0) or 0)
        if mastery >= MASTERY_THRESHOLD:
            mastered += 1
        if mastery >= READY_THRESHOLD:
            ready += 1
        if (
            int(state.get("due_at", 0) or 0) > 0
            and mastery >= READY_THRESHOLD
            and mastery < MASTERY_THRESHOLD
        ):
            due_later += 1
        overall_mastery_sum += mastery
        if attempts > 0 and mastery >= 0.15:
            engaged += 1
            engaged_mastery_sum += mastery

    coverage = (engaged / total) if total else 0.0
    engaged_average_mastery = (engaged_mastery_sum / engaged) if engaged else 0.0
    overall_average_mastery = (overall_mastery_sum / total) if total else 0.0
    progress_fraction = (
        (0.10 * coverage)
        + (0.35 * engaged_average_mastery)
        + (0.55 * overall_average_mastery)
    ) if total else 0.0
    if total and mastered == total:
        percent = 100
    else:
        percent = min(99, round(progress_fraction * 100)) if total else 0
    return {
        "name": scope_name,
        "question_count": total,
        "mastered_count": mastered,
        "ready_count": ready,
        "engaged_count": engaged,
        "due_later_count": due_later,
        "percent_learned": percent,
        "percent_fraction": (percent / 100) if total else 0.0,
        "remaining_count": max(0, total - ready),
        "coverage_fraction": coverage,
        "engaged_average_mastery": engaged_average_mastery,
        "overall_average_mastery": overall_average_mastery,
    }


def summary_for_scope(scope_name: str, question_ids: list[int], progress: dict) -> dict:
    summary = progress_for_scope(scope_name, question_ids, progress)
    if scope_name == "__all__":
        summary["headline"] = f"You have reached {summary['percent_learned']}% learning progress across all Knowledge Areas"
    else:
        summary["headline"] = f"You have reached {summary['percent_learned']}% learning progress in {scope_name}"
    summary["detail"] = (
        f"{summary['ready_count']} of {summary['question_count']} questions ready"
    )
    return summary
