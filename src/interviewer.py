def get_next_question(stage: str, profile: dict, history: list) -> str:
    """Placeholder interview controller for Day 1."""
    if stage == "intro":
        return "请你做一个简短的自我介绍。"
    if stage == "project":
        return "请介绍你简历中最重要的一个项目，包括背景、职责和技术栈。"
    if stage == "basic":
        return "请解释一个你熟悉的计算机基础知识点，并结合项目说明它的应用。"
    return "请总结一下你认为自己最适合该岗位的原因。"
