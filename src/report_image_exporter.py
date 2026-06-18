from __future__ import annotations

from datetime import datetime
from io import BytesIO
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - handled at runtime in Streamlit.
    Image = None
    ImageDraw = None
    ImageFont = None


BG = "#F7F7F8"
CARD = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#111827"
MUTED = "#6B7280"
SOFT = "#F3F4F6"
WARNING_BG = "#FFFBEB"
WARNING_BORDER = "#FDE68A"
MAX_FULL_HEIGHT = 20000


FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


QUESTION_TYPE_LABELS = {
    "intro": "自我介绍",
    "project": "项目问题",
    "project_followup": "项目追问",
    "rag_basic": "基础知识题",
    "rag_followup": "知识点追问",
    "basic": "基础题",
    "comprehensive": "综合问题",
    "end": "结束提示",
    "unknown": "未标注题型",
}


_FONT_WARNING = ""


def get_font_warning() -> str:
    return _FONT_WARNING


def _require_pillow() -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("Pillow 未安装，无法导出 PNG。请运行 pip install -r requirements.txt。")


def _font(size: int, bold: bool = False):
    global _FONT_WARNING
    _require_pillow()
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    _FONT_WARNING = "未检测到中文字体，导出的 PNG 可能无法正常显示中文。"
    return ImageFont.load_default()


def _text(value: Any, default: str = "暂无数据") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _items(value: Any, limit: int = 6) -> List[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict):
            parts = [item.get("title"), item.get("evidence"), item.get("suggestion")]
            text = "；".join(str(part).strip() for part in parts if str(part or "").strip())
        else:
            text = str(item or "").strip()
        if text:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _question_type_label(value: str) -> str:
    return QUESTION_TYPE_LABELS.get(str(value or "unknown"), str(value or "未标注题型"))


def _score(value: Any) -> float:
    try:
        return max(0.0, min(100.0, float(value or 0)))
    except Exception:
        return 0.0


class ReportCanvas:
    def __init__(self, width: int = 1200, max_height: int = MAX_FULL_HEIGHT):
        _require_pillow()
        self.width = width
        self.max_height = max_height
        self.margin = 48
        self.gap = 18
        self.y = self.margin
        self.truncated = False
        self.image = Image.new("RGB", (width, max_height), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.font_title = _font(44)
        self.font_h2 = _font(28)
        self.font_h3 = _font(22)
        self.font_body = _font(20)
        self.font_small = _font(16)
        self.font_score = _font(72)

    def _can_fit(self, height: int) -> bool:
        if self.y + height + self.margin <= self.max_height:
            return True
        self.truncated = True
        return False

    def line_height(self, font) -> int:
        bbox = self.draw.textbbox((0, 0), "国Ag", font=font)
        return bbox[3] - bbox[1] + 8

    def wrap(self, text: Any, font, max_width: int, max_lines: int | None = None) -> List[str]:
        text = _text(text, "")
        lines: List[str] = []
        paragraphs = text.splitlines() or [""]
        for paragraph_index, paragraph in enumerate(paragraphs):
            current = ""
            for char_index, char in enumerate(paragraph):
                trial = current + char
                if self.draw.textlength(trial, font=font) <= max_width:
                    current = trial
                else:
                    if current:
                        lines.append(current)
                    current = char
                    if max_lines and len(lines) >= max_lines:
                        lines[-1] = lines[-1].rstrip("，。；、,.; ") + "..."
                        return lines
            lines.append(current)
            if max_lines and len(lines) >= max_lines:
                if paragraph_index < len(paragraphs) - 1:
                    lines[-1] = lines[-1].rstrip("，。；、,.; ") + "..."
                return lines
        return lines

    def text_block(self, x: int, y: int, text: Any, font, color: str, max_width: int, max_lines: int | None = None) -> int:
        line_h = self.line_height(font)
        current_y = y
        for line in self.wrap(text, font, max_width, max_lines=max_lines):
            self.draw.text((x, current_y), line, font=font, fill=color)
            current_y += line_h
        return current_y

    def title(self, title: str, subtitle: str = ""):
        self.draw.text((self.margin, self.y), title, font=self.font_title, fill=TEXT)
        self.y += self.line_height(self.font_title) + 8
        if subtitle:
            self.y = self.text_block(self.margin, self.y, subtitle, self.font_body, MUTED, self.width - self.margin * 2, 2)
        self.y += 20

    def section_title(self, title: str):
        if not self._can_fit(56):
            return
        self.draw.text((self.margin, self.y), title, font=self.font_h2, fill=TEXT)
        self.y += self.line_height(self.font_h2) + 6

    def rounded_card(self, height: int, fill: str = CARD, border: str = BORDER) -> Tuple[int, int, int, int] | None:
        if not self._can_fit(height + self.gap):
            return None
        x1, y1 = self.margin, self.y
        x2, y2 = self.width - self.margin, self.y + height
        self.draw.rounded_rectangle((x1 + 4, y1 + 6, x2 + 4, y2 + 6), radius=18, fill="#E9EAEE")
        self.draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=fill, outline=border, width=2)
        self.y = y2 + self.gap
        return x1, y1, x2, y2

    def metric_cards(self, metrics: List[Tuple[str, Any]], columns: int = 4):
        if not metrics:
            return
        card_w = (self.width - self.margin * 2 - (columns - 1) * 14) // columns
        card_h = 118
        rows = [metrics[i:i + columns] for i in range(0, len(metrics), columns)]
        for row in rows:
            if not self._can_fit(card_h + 18):
                return
            y = self.y
            for idx, (label, value) in enumerate(row):
                x = self.margin + idx * (card_w + 14)
                self.draw.rounded_rectangle((x + 3, y + 5, x + card_w + 3, y + card_h + 5), radius=16, fill="#E9EAEE")
                self.draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=16, fill=CARD, outline=BORDER, width=2)
                self.draw.text((x + 18, y + 18), _text(label, ""), font=self.font_small, fill=MUTED)
                self.text_block(x + 18, y + 48, _text(value, ""), self.font_h2, TEXT, card_w - 36, 1)
            self.y += card_h + 18

    def radar_chart(self, dimension_details: Dict[str, Any]):
        self.section_title("五维度能力雷达图")
        items = []
        for dim, detail in (dimension_details or {}).items():
            if isinstance(detail, dict):
                items.append((str(dim), _score(detail.get("score", 0))))
            else:
                items.append((str(dim), _score(detail)))
        if len(items) < 3:
            self.paragraph_card("暂无足够维度数据，无法生成雷达图。", max_lines=2)
            return

        rect = self.rounded_card(470)
        if not rect:
            return
        x1, y1, x2, y2 = rect
        cx = (x1 + x2) // 2
        cy = y1 + 230
        radius = 145
        count = len(items)

        def point(index: int, value: float):
            angle = -math.pi / 2 + 2 * math.pi * index / count
            r = radius * value
            return cx + r * math.cos(angle), cy + r * math.sin(angle)

        for level in range(1, 6):
            level_points = [point(i, level / 5) for i in range(count)]
            self.draw.polygon(level_points, outline=BORDER)

        for i in range(count):
            axis_end = point(i, 1)
            self.draw.line((cx, cy, axis_end[0], axis_end[1]), fill=BORDER, width=2)

        score_points = [point(i, score / 100) for i, (_, score) in enumerate(items)]
        self.draw.polygon(score_points, fill="#D1D5DB", outline=TEXT)
        self.draw.line(score_points + [score_points[0]], fill=TEXT, width=3)
        for px, py in score_points:
            self.draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=TEXT)

        for i, (dim, score) in enumerate(items):
            lx, ly = point(i, 1.28)
            label = dim
            if len(label) > 12:
                label = label[:12]
            label = f"{label} {score:g}"
            bbox = self.draw.textbbox((0, 0), label, font=self.font_small)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            self.draw.text((lx - tw / 2, ly - th / 2), label, font=self.font_small, fill=TEXT)

        self.draw.text((x1 + 24, y2 - 48), "说明：雷达图展示五个评分维度的相对表现，外圈代表 100 分。", font=self.font_small, fill=MUTED)

    def paragraph_card(self, text: Any, max_lines: int = 5, warning: bool = False):
        font = self.font_body
        max_width = self.width - self.margin * 2 - 44
        lines = self.wrap(text, font, max_width, max_lines=max_lines)
        height = 36 + len(lines) * self.line_height(font)
        rect = self.rounded_card(height, fill=WARNING_BG if warning else CARD, border=WARNING_BORDER if warning else BORDER)
        if not rect:
            return
        x1, y1, x2, _ = rect
        current_y = y1 + 18
        for line in lines:
            self.draw.text((x1 + 22, current_y), line, font=font, fill=TEXT)
            current_y += self.line_height(font)

    def bullet_section(
        self,
        title: str,
        items: Iterable[Any],
        limit: int = 6,
        max_lines_per_item: int | None = None,
    ):
        self.section_title(title)
        bullets = _items(list(items), limit=limit) or ["暂无数据"]
        max_width = self.width - self.margin * 2 - 60
        line_count = sum(
            len(self.wrap("- " + item, self.font_body, max_width, max_lines_per_item))
            for item in bullets
        )
        height = 34 + line_count * self.line_height(self.font_body)
        rect = self.rounded_card(height)
        if not rect:
            return
        x1, y1, _, _ = rect
        current_y = y1 + 18
        for item in bullets:
            for line in self.wrap("- " + item, self.font_body, max_width, max_lines_per_item):
                self.draw.text((x1 + 24, current_y), line, font=self.font_body, fill=TEXT)
                current_y += self.line_height(self.font_body)

    def dimension_bars(self, dimension_details: Dict[str, Any]):
        self.section_title("五维度评分")
        items = []
        for dim, detail in (dimension_details or {}).items():
            if isinstance(detail, dict):
                items.append((dim, detail.get("score", 0), detail.get("weight", "")))
            else:
                items.append((dim, detail, ""))
        if not items:
            items = [("暂无维度数据", 0, "")]
        row_h = 56
        height = 30 + len(items) * row_h
        rect = self.rounded_card(height)
        if not rect:
            return
        x1, y1, x2, _ = rect
        current_y = y1 + 20
        bar_x = x1 + 360
        bar_w = x2 - bar_x - 110
        for dim, score, weight in items:
            value = _score(score)
            self.text_block(x1 + 24, current_y, f"{dim} {weight}", self.font_body, TEXT, 320, 1)
            self.draw.rounded_rectangle((bar_x, current_y + 10, bar_x + bar_w, current_y + 28), radius=9, fill=SOFT)
            self.draw.rounded_rectangle((bar_x, current_y + 10, bar_x + int(bar_w * value / 100), current_y + 28), radius=9, fill=TEXT)
            self.draw.text((bar_x + bar_w + 18, current_y + 2), f"{value:g}", font=self.font_body, fill=TEXT)
            current_y += row_h

    def evidence_section(self, dimension_details: Dict[str, Any], limit_per_dim: int = 2):
        self.section_title("评分依据")
        bullets = []
        for dim, detail in (dimension_details or {}).items():
            evidence = detail.get("evidence", []) if isinstance(detail, dict) else []
            for item in _items(evidence, limit=limit_per_dim):
                bullets.append(f"{dim}：{item}")
        self.bullet_section("", bullets or ["暂无评分依据"], limit=10)

    def footer(self):
        text = f"AI 模拟面试与能力提升平台 · 本报告由系统自动生成，仅供学习与面试训练参考 · {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if self.truncated:
            self.paragraph_card("报告内容较长，完整内容请下载 Markdown 报告查看。", warning=True)
        self.draw.text((self.margin, self.y + 12), text, font=self.font_small, fill=MUTED)
        self.y += 56

    def png_bytes(self) -> bytes:
        final_height = min(self.max_height, max(self.y + self.margin, 900))
        cropped = self.image.crop((0, 0, self.width, final_height))
        out = BytesIO()
        cropped.save(out, format="PNG", optimize=True)
        return out.getvalue()


def _summary(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("interview_summary", {}) or {}


def _distribution(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("question_distribution", {}) or {}


def _stability(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("answer_stability", {}) or {}


def _ability(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("role_ability_coverage", {}) or {}


def _overview_metrics(report: Dict[str, Any]) -> List[Tuple[str, Any]]:
    summary = _summary(report)
    distribution = _distribution(report)
    status = "阶段性报告" if report.get("is_incomplete_interview") else "完整报告"
    return [
        ("目标岗位", report.get("target_role") or "未明确"),
        ("面试难度", report.get("difficulty") or "未明确"),
        ("答题数量", summary.get("answer_count", 0)),
        ("基础知识题", summary.get("basic_question_count", 0)),
        ("项目深挖题", summary.get("project_question_count", 0)),
        ("LLM 出题", distribution.get("llm_question_count", 0)),
        ("备用出题", distribution.get("fallback_question_count", 0)),
        ("报告状态", status),
    ]


def generate_full_report_png(report: Dict[str, Any], interview_records: List[Dict[str, Any]] | None = None) -> bytes:
    canvas = ReportCanvas(width=1200, max_height=MAX_FULL_HEIGHT)
    subtitle = (
        f"生成时间：{_text(report.get('generated_at'), '未记录')}    "
        f"目标岗位：{_text(report.get('target_role'), '未明确')}    "
        f"面试难度：{_text(report.get('difficulty'), '未明确')}"
    )
    canvas.title("AI 模拟面试评分报告", subtitle)

    if report.get("is_incomplete_interview"):
        canvas.paragraph_card(
            report.get("incomplete_report_warning")
            or "本次面试尚未完整完成，当前评分报告仅基于已回答内容生成，结果仅供阶段性参考。建议完成完整轮次后再生成正式报告。",
            warning=True,
            max_lines=4,
        )

    canvas.metric_cards([
        ("总分", f"{report.get('total_score', 0)} / 100"),
        ("等级", report.get("level", "未评级")),
        ("目标岗位", report.get("target_role") or "未明确"),
        ("答题数量", _summary(report).get("answer_count", 0)),
    ])

    canvas.section_title("本次面试概览")
    canvas.metric_cards(_overview_metrics(report))
    canvas.radar_chart(report.get("dimension_details", {}) or report.get("dimension_scores", {}))
    canvas.dimension_bars(report.get("dimension_details", {}) or report.get("dimension_scores", {}))
    canvas.evidence_section(report.get("dimension_details", {}))

    distribution = _distribution(report)
    canvas.section_title("问题难度与类型分布")
    canvas.paragraph_card(distribution.get("summary") or "暂无问题分布摘要。", max_lines=6)
    type_metrics = [
        (_question_type_label(qtype), f"{count} 题")
        for qtype, count in (distribution.get("type_counts", {}) or {}).items()
    ]
    canvas.metric_cards(type_metrics or [("题型分布", "暂无数据")], columns=4)

    stability = _stability(report)
    canvas.section_title("回答稳定性分析")
    canvas.paragraph_card(stability.get("summary") or "暂无回答稳定性摘要。", max_lines=6)
    canvas.metric_cards([
        ("平均覆盖率", stability.get("average_coverage", 0)),
        ("高覆盖回答", stability.get("high_coverage_count", 0)),
        ("低覆盖回答", stability.get("low_coverage_count", 0)),
    ], columns=3)

    ability = _ability(report)
    canvas.section_title("岗位能力覆盖图")
    canvas.paragraph_card(ability.get("summary") or "暂无岗位能力覆盖摘要。", max_lines=6)
    canvas.bullet_section("已覆盖能力", ability.get("covered_abilities", []) or ["暂无明显覆盖"], limit=8)
    canvas.bullet_section("建议加强能力", ability.get("missing_or_weak_abilities", []) or ["暂无明显薄弱项"], limit=8)

    canvas.bullet_section("表现亮点", report.get("strengths", []), limit=6)
    canvas.bullet_section("主要问题", report.get("main_problems", []), limit=6)
    canvas.bullet_section("简历与岗位匹配建议", report.get("resume_optimization_suggestions", []), limit=6)
    canvas.bullet_section("错题与薄弱知识点总结", report.get("weak_point_cards") or report.get("weak_points_summary", []), limit=8)
    canvas.bullet_section("学习建议推荐", report.get("learning_recommendations", []), limit=6)
    canvas.bullet_section("后续提升建议", report.get("recommendations", []), limit=6)
    canvas.footer()
    return canvas.png_bytes()


def generate_summary_poster_png(report: Dict[str, Any], interview_records: List[Dict[str, Any]] | None = None) -> bytes:
    canvas = ReportCanvas(width=1080, max_height=2200)
    canvas.margin = 46
    canvas.title(
        "AI 模拟面试评分报告",
        f"{_text(report.get('target_role'), '未明确')} / {_text(report.get('difficulty'), '未明确')} / {_text(report.get('generated_at'), '未记录')}",
    )

    if report.get("is_incomplete_interview"):
        canvas.paragraph_card(
            report.get("incomplete_report_warning")
            or "本次面试尚未完整完成，当前报告仅供阶段性参考。",
            warning=True,
            max_lines=3,
        )

    rect = canvas.rounded_card(230)
    if rect:
        x1, y1, x2, _ = rect
        score = _text(report.get("total_score", 0), "0")
        level = _text(report.get("level"), "未评级")
        canvas.draw.text((x1 + 36, y1 + 32), "总分", font=canvas.font_h2, fill=MUTED)
        canvas.draw.text((x1 + 36, y1 + 78), score, font=canvas.font_score, fill=TEXT)
        canvas.draw.text((x1 + 360, y1 + 96), level, font=canvas.font_title, fill=TEXT)
        canvas.text_block(x1 + 36, y1 + 168, "评分由本地规则计算，LLM 仅用于文字润色。", canvas.font_body, MUTED, x2 - x1 - 72, 1)

    summary = _summary(report)
    distribution = _distribution(report)
    match_score = ""
    for dim, detail in (report.get("dimension_details", {}) or {}).items():
        if "匹配" in str(dim):
            match_score = detail.get("score") if isinstance(detail, dict) else detail
            break
    canvas.metric_cards([
        ("答题数量", summary.get("answer_count", 0)),
        ("基础知识题", summary.get("basic_question_count", 0)),
        ("项目深挖题", summary.get("project_question_count", 0)),
        ("岗位匹配度", match_score or "暂无"),
    ], columns=4)

    canvas.dimension_bars(report.get("dimension_details", {}) or report.get("dimension_scores", {}))

    type_metrics = [
        (_question_type_label(qtype), f"{count} 题")
        for qtype, count in (distribution.get("type_counts", {}) or {}).items()
    ]
    canvas.section_title("问题分布")
    canvas.metric_cards(type_metrics[:4] or [("题型分布", "暂无数据")], columns=3)

    canvas.bullet_section("关键亮点", report.get("strengths", []), limit=3, max_lines_per_item=2)
    weak_focus = report.get("weak_point_cards") or report.get("main_problems") or report.get("weak_points_summary", [])
    canvas.bullet_section("改进重点", weak_focus, limit=2, max_lines_per_item=2)
    canvas.bullet_section("学习建议", report.get("learning_recommendations", []), limit=3, max_lines_per_item=2)
    canvas.footer()
    return canvas.png_bytes()
