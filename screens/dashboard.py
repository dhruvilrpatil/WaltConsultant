"""Dashboard screen for WaltConsultant styled to premium overview layout."""

from __future__ import annotations

from datetime import date, datetime
from math import atan2, degrees, hypot
import tkinter as tk

from components.button import WaltButton
from components.modal import WaltModal
from components.table import WaltTable
from components.toast import WaltToast
from models.loan import LOAN_MODEL
from models.repayment import REPAYMENT_MODEL
from utils.formatters import format_inr
from utils.theme import is_dark_mode

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


class RoundedCard(tk.Frame):
    def __init__(
        self,
        parent,
        *,
        outer_bg: str,
        card_bg: str,
        border_color: str,
        radius: int = 18,
        **kwargs,
    ):
        super().__init__(parent, bg=outer_bg, bd=0, highlightthickness=0, **kwargs)
        self.outer_bg = outer_bg
        self.card_bg = card_bg
        self.border_color = border_color
        self.radius = radius

        self.background = tk.Canvas(self, bg=outer_bg, highlightthickness=0, bd=0)
        self.background.place(x=0, y=0, relwidth=1, relheight=1)

        self.content = tk.Frame(self, bg=card_bg)
        self.content.pack(fill="both", expand=True)
        self._ensure_content_front()

        self.bind("<Configure>", self._redraw)
        self.after(0, self._redraw)

    def _ensure_content_front(self) -> None:
        try:
            self.tk.call("lower", self.background._w, self.content._w)
        except Exception:
            pass
        self.content.lift()

    def _draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, radius: int) -> None:
        self.background.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=self.card_bg, outline="", tags="card")
        self.background.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=self.card_bg, outline="", tags="card")
        self.background.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=self.card_bg, outline="", tags="card")
        self.background.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=self.card_bg, outline="", tags="card")
        self.background.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=self.card_bg, outline="", tags="card")
        self.background.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=self.card_bg, outline="", tags="card")

        self.background.create_line(x1 + radius, y1, x2 - radius, y1, fill=self.border_color, width=1, tags="card")
        self.background.create_line(x1 + radius, y2, x2 - radius, y2, fill=self.border_color, width=1, tags="card")
        self.background.create_line(x1, y1 + radius, x1, y2 - radius, fill=self.border_color, width=1, tags="card")
        self.background.create_line(x2, y1 + radius, x2, y2 - radius, fill=self.border_color, width=1, tags="card")
        self.background.create_arc(x1, y1, x1 + radius * 2, y1 + radius * 2, start=90, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self.background.create_arc(x2 - radius * 2, y1, x2, y1 + radius * 2, start=0, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self.background.create_arc(x1, y2 - radius * 2, x1 + radius * 2, y2, start=180, extent=90, style="arc", outline=self.border_color, width=1, tags="card")
        self.background.create_arc(x2 - radius * 2, y2 - radius * 2, x2, y2, start=270, extent=90, style="arc", outline=self.border_color, width=1, tags="card")

    def _redraw(self, _event=None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 6 or height < 6:
            return

        radius = min(self.radius, (width - 2) // 2, (height - 2) // 2)
        self.background.delete("card")
        self._draw_rounded_rect(1, 1, width - 1, height - 1, radius)
        self.background.lower("card")
        self._ensure_content_front()


class DashboardScreen(tk.Frame):
    PAGE_BG = "#F3F4F8"
    CARD_BG = "#FFFFFF"
    CARD_BORDER = "#EAEDF2"
    TEXT_PRIMARY = "#191F28"
    TEXT_SECONDARY = "#7A8594"
    PRIMARY = "#135DBE"

    def __init__(self, parent, current_user_id: int | None):
        self._configure_theme_tokens()
        super().__init__(parent, bg=self.PAGE_BG)
        self.current_user_id = current_user_id
        self._trend_card_height = 430
        self._portfolio_card_height = 500
        self._portfolio_plot_height = 238
        self.selected_due: dict | None = None
        self._due_row_frames: list[tk.Frame] = []
        self._due_raw: list[dict] = []
        self._mousewheel_bound = False
        self._compact_mode: bool | None = None

        self._build()
        self.refresh()

    def _configure_theme_tokens(self) -> None:
        if is_dark_mode():
            self.PAGE_BG = "#131722"
            self.CARD_BG = "#1A2231"
            self.CARD_BORDER = "#2A3447"
            self.TEXT_PRIMARY = "#E9EEF7"
            self.TEXT_SECONDARY = "#A8B2C5"
            self.PRIMARY = "#5AA0FF"
            self.ACTION_LINK = "#7FB3FF"
            self.TABLE_HEADER_BG = "#253149"
            self.TABLE_HEADER_FG = "#CDD7E8"
            self.ROW_DIVIDER = "#2A3447"
            self.SELECTED_ROW_BG = "#2E4568"
            self.AXIS_TEXT = "#93A3BD"
            self.AXIS_LINE = "#33405A"
            self.MUTED_BAR = "#3C4C66"
        else:
            self.PAGE_BG = "#F3F4F8"
            self.CARD_BG = "#FFFFFF"
            self.CARD_BORDER = "#EAEDF2"
            self.TEXT_PRIMARY = "#191F28"
            self.TEXT_SECONDARY = "#7A8594"
            self.PRIMARY = "#135DBE"
            self.ACTION_LINK = "#145DC0"
            self.TABLE_HEADER_BG = "#F8F9FC"
            self.TABLE_HEADER_FG = "#9AA4B2"
            self.ROW_DIVIDER = "#EFF2F6"
            self.SELECTED_ROW_BG = "#EDF3FD"
            self.AXIS_TEXT = "#9DA6B4"
            self.AXIS_LINE = "#E5EAF0"
            self.MUTED_BAR = "#C8D3DF"

    def _build(self) -> None:
        self.scroll_canvas = tk.Canvas(self, bg=self.PAGE_BG, highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.scroll_canvas, bg=self.PAGE_BG)
        self._content_window = self.scroll_canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scroll_canvas.bind("<Enter>", self._bind_mousewheel)
        self.scroll_canvas.bind("<Leave>", self._unbind_mousewheel)
        self.bind("<Destroy>", self._on_destroy)

        self.content.configure(padx=18, pady=14)

        self._build_metric_row()
        self._build_chart_row()
        self._build_table_row()
        self.after(0, lambda: self._apply_compact_layout(self.winfo_width()))

    def _on_content_configure(self, _event) -> None:
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.scroll_canvas.itemconfigure(self._content_window, width=event.width)
        if hasattr(self, "recent_header") and hasattr(self, "trend_card"):
            self._apply_compact_layout(event.width)

    def _apply_compact_layout(self, width: int) -> None:
        compact = width < 1240
        if self._compact_mode == compact:
            return
        self._compact_mode = compact

        self.content.configure(padx=10 if compact else 18, pady=10 if compact else 14)
        self.chart_row.pack_configure(pady=(10, 10) if compact else (14, 14))

        self.metric_active["card"].pack_configure(padx=(0, 6 if compact else 10))
        self.metric_disbursed["card"].pack_configure(padx=(0, 6 if compact else 10))
        self.metric_overdue["card"].pack_configure(padx=(0, 6 if compact else 10))

        self.recent_header.pack_configure(padx=14 if compact else 18, pady=(10, 6) if compact else (14, 8))
        self.due_header.pack_configure(padx=14 if compact else 18, pady=(10, 6) if compact else (14, 8))
        self.recent_table_header.pack_configure(padx=12 if compact else 14)
        self.due_table_header.pack_configure(padx=12 if compact else 14)
        self.recent_rows_host.pack_configure(padx=12 if compact else 14)
        self.due_rows_host.pack_configure(padx=12 if compact else 14)

        self.trend_card.pack_forget()
        self.portfolio_card.pack_forget()
        if compact:
            self._trend_card_height = 420
            self._portfolio_card_height = 470
            self._portfolio_plot_height = 214
            self.trend_card.configure(height=self._trend_card_height)
            self.portfolio_card.configure(width=0, height=self._portfolio_card_height)
            self.portfolio_plot_holder.configure(height=self._portfolio_plot_height)
            self.trend_card.pack(side="top", fill="both", expand=True, padx=0, pady=(0, 10))
            self.portfolio_card.pack(side="top", fill="x")
        else:
            self._trend_card_height = 430
            self._portfolio_card_height = 500
            self._portfolio_plot_height = 238
            self.trend_card.configure(height=self._trend_card_height)
            self.portfolio_card.configure(width=430, height=self._portfolio_card_height)
            self.portfolio_plot_holder.configure(height=self._portfolio_plot_height)
            self.trend_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self.portfolio_card.pack(side="left", fill="both")

        self.recent_card.pack_forget()
        self.due_card.pack_forget()
        if compact:
            self.recent_card.pack(side="top", fill="both", expand=True, pady=(0, 10))
            self.due_card.pack(side="top", fill="both", expand=True)
        else:
            self.recent_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self.due_card.pack(side="left", fill="both", expand=True)

    def _on_mousewheel(self, event) -> None:
        steps = -int(event.delta / 120) if event.delta else 0
        if steps == 0 and event.delta:
            steps = -1 if event.delta > 0 else 1
        if steps:
            self.scroll_canvas.yview_scroll(steps, "units")

    def _bind_mousewheel(self, _event) -> None:
        if self._mousewheel_bound:
            return
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._mousewheel_bound = True

    def _unbind_mousewheel(self, _event) -> None:
        if not self._mousewheel_bound:
            return
        self.scroll_canvas.unbind_all("<MouseWheel>")
        self._mousewheel_bound = False

    def _on_destroy(self, _event) -> None:
        if self._mousewheel_bound:
            self.scroll_canvas.unbind_all("<MouseWheel>")
            self._mousewheel_bound = False

    def _build_metric_row(self) -> None:
        self.metrics_row = tk.Frame(self.content, bg=self.PAGE_BG)
        self.metrics_row.pack(fill="x")

        self.metric_active = self._create_metric_card(
            self.metrics_row,
            title="Total Active Loans",
            icon="D",
            icon_bg="#E8EFFA",
            icon_fg="#245FD4",
            trend_text="+12%",
            trend_bg="#E8FAEF",
            trend_fg="#0D8E4C",
        )
        self.metric_active["card"].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.metric_disbursed = self._create_metric_card(
            self.metrics_row,
            title="Total Disbursed Amount",
            icon="Rs",
            icon_bg="#EDF0FD",
            icon_fg="#3558CC",
            trend_text="+8.4%",
            trend_bg="#E8FAEF",
            trend_fg="#0D8E4C",
        )
        self.metric_disbursed["card"].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.metric_overdue = self._create_metric_card(
            self.metrics_row,
            title="Overdue EMIs",
            icon="!",
            icon_bg="#FCECEE",
            icon_fg="#CA2D3C",
            trend_text="+2.1%",
            trend_bg="#FCECEE",
            trend_fg="#CA2D3C",
            danger_left_border=True,
        )
        self.metric_overdue["card"].pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.metric_collection = self._create_metric_card(
            self.metrics_row,
            title="Collections This Month",
            icon="*",
            icon_bg="#F2ECFA",
            icon_fg="#7D3DA8",
            trend_text="+15%",
            trend_bg="#E8FAEF",
            trend_fg="#0D8E4C",
        )
        self.metric_collection["card"].pack(side="left", fill="x", expand=True)

    def _create_metric_card(
        self,
        parent: tk.Widget,
        title: str,
        icon: str,
        icon_bg: str,
        icon_fg: str,
        trend_text: str,
        trend_bg: str,
        trend_fg: str,
        danger_left_border: bool = False,
    ) -> dict[str, tk.Widget]:
        card = RoundedCard(
            parent,
            outer_bg=self.PAGE_BG,
            card_bg=self.CARD_BG,
            border_color=self.CARD_BORDER,
            radius=16,
        )
        if danger_left_border:
            tk.Frame(card.content, bg="#D72F44", width=3).pack(side="left", fill="y")

        inner = tk.Frame(card.content, bg=self.CARD_BG)
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        top = tk.Frame(inner, bg=self.CARD_BG)
        top.pack(fill="x")

        icon_label = tk.Label(top, text=icon, bg=icon_bg, fg=icon_fg, font=("SF Pro Rounded", 10, "bold"), padx=9, pady=5)
        icon_label.pack(side="left")

        trend_label = tk.Label(top, text=trend_text, bg=trend_bg, fg=trend_fg, font=("SF Pro Rounded", 8, "bold"), padx=7, pady=2)
        trend_label.pack(side="right")

        title_label = tk.Label(inner, text=title, bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11))
        title_label.pack(anchor="w", pady=(10, 2))

        value_label = tk.Label(inner, text="-", bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 28, "bold"))
        value_label.pack(anchor="w")

        subtitle_label = tk.Label(inner, text="", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 10))
        subtitle_label.pack(anchor="w", pady=(3, 0))

        return {
            "card": card,
            "value": value_label,
            "subtitle": subtitle_label,
            "trend": trend_label,
        }

    def _build_chart_row(self) -> None:
        self.chart_row = tk.Frame(self.content, bg=self.PAGE_BG)
        self.chart_row.pack(fill="x", pady=(14, 14))

        self.trend_card = RoundedCard(
            self.chart_row,
            outer_bg=self.PAGE_BG,
            card_bg=self.CARD_BG,
            border_color=self.CARD_BORDER,
            radius=20,
            height=self._trend_card_height,
        )
        self.trend_card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.trend_card.pack_propagate(False)

        trend_header = tk.Frame(self.trend_card.content, bg=self.CARD_BG)
        trend_header.pack(fill="x", padx=20, pady=(16, 8))

        trend_title_wrap = tk.Frame(trend_header, bg=self.CARD_BG)
        trend_title_wrap.pack(side="left")
        tk.Label(trend_title_wrap, text="Loan Disbursement Trend", bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 18, "bold")).pack(anchor="w")
        tk.Label(trend_title_wrap, text="Monthly breakdown of capital allocation", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", pady=(1, 0))

        trend_view = tk.Label(trend_header, text="View", bg=self.CARD_BG, fg=self.ACTION_LINK, cursor="hand2", font=("SF Pro Rounded", 10, "bold"))
        trend_view.pack(side="right")
        trend_view.bind("<Button-1>", lambda _event: self._open_trend_all_modal())

        self.trend_plot_holder = tk.Frame(self.trend_card.content, bg=self.CARD_BG)
        self.trend_plot_holder.pack(fill="both", expand=True, padx=14, pady=(2, 12))

        self.portfolio_card = RoundedCard(
            self.chart_row,
            outer_bg=self.PAGE_BG,
            card_bg=self.CARD_BG,
            border_color=self.CARD_BORDER,
            radius=20,
            width=430,
            height=self._portfolio_card_height,
        )
        self.portfolio_card.pack(side="left", fill="both")
        self.portfolio_card.pack_propagate(False)

        portfolio_header = tk.Frame(self.portfolio_card.content, bg=self.CARD_BG)
        portfolio_header.pack(fill="x", padx=20, pady=(16, 0))

        portfolio_title_wrap = tk.Frame(portfolio_header, bg=self.CARD_BG)
        portfolio_title_wrap.pack(side="left")
        tk.Label(portfolio_title_wrap, text="Loan Portfolio", bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 18, "bold")).pack(anchor="w")
        tk.Label(portfolio_title_wrap, text="Distribution by loan type", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", pady=(4, 0))

        portfolio_view = tk.Label(portfolio_header, text="View", bg=self.CARD_BG, fg=self.ACTION_LINK, cursor="hand2", font=("SF Pro Rounded", 10, "bold"))
        portfolio_view.pack(side="right")
        portfolio_view.bind("<Button-1>", lambda _event: self._open_portfolio_all_modal())

        self.portfolio_kpi_row = tk.Frame(self.portfolio_card.content, bg=self.CARD_BG)
        self.portfolio_kpi_row.pack(fill="x", padx=14, pady=(8, 2))

        self.portfolio_plot_holder = tk.Frame(self.portfolio_card.content, bg=self.CARD_BG, height=self._portfolio_plot_height)
        self.portfolio_plot_holder.pack(fill="x", expand=False, padx=12, pady=(8, 0))
        self.portfolio_plot_holder.pack_propagate(False)

        self.portfolio_legend = tk.Frame(self.portfolio_card.content, bg=self.CARD_BG)
        self.portfolio_legend.pack(fill="both", expand=True, padx=18, pady=(6, 16))

        self.portfolio_legend_canvas = tk.Canvas(self.portfolio_legend, bg=self.CARD_BG, highlightthickness=0, bd=0)
        self.portfolio_legend_scrollbar = tk.Scrollbar(self.portfolio_legend, orient="vertical", command=self.portfolio_legend_canvas.yview, width=9)
        self.portfolio_legend_canvas.configure(yscrollcommand=self.portfolio_legend_scrollbar.set)
        self.portfolio_legend_canvas.pack(side="left", fill="both", expand=True)
        self.portfolio_legend_scrollbar.pack(side="right", fill="y")

        self.portfolio_legend_body = tk.Frame(self.portfolio_legend_canvas, bg=self.CARD_BG)
        self._portfolio_legend_window = self.portfolio_legend_canvas.create_window((0, 0), window=self.portfolio_legend_body, anchor="nw")
        self.portfolio_legend_body.bind("<Configure>", lambda _e: self.portfolio_legend_canvas.configure(scrollregion=self.portfolio_legend_canvas.bbox("all")))
        self.portfolio_legend_canvas.bind("<Configure>", lambda e: self.portfolio_legend_canvas.itemconfigure(self._portfolio_legend_window, width=e.width))

    def _build_trend_series(self, trend: list[dict]) -> tuple[list[str], list[float]]:
        month_totals: dict[int, float] = {}
        latest_index = -1

        for row in trend:
            try:
                month_dt = datetime.strptime(str(row.get("month", "")), "%Y-%m")
            except ValueError:
                continue

            month_index = month_dt.year * 12 + month_dt.month - 1
            month_totals[month_index] = month_totals.get(month_index, 0.0) + float(row.get("amount", 0) or 0)
            latest_index = max(latest_index, month_index)

        if latest_index < 0:
            return [], []
        labels: list[str] = []
        values: list[float] = []
        for month_index in range(latest_index - 6, latest_index + 1):
            year = month_index // 12
            month = (month_index % 12) + 1
            labels.append(datetime(year, month, 1).strftime("%b").upper())
            values.append(month_totals.get(month_index, 0.0))

        return labels, values

    def _render_portfolio_kpis(self, total_outstanding: float, total_overdue: float, overall_delinquency: float) -> None:
        for child in self.portfolio_kpi_row.winfo_children():
            child.destroy()

        if is_dark_mode():
            neutral_bg = "#243247"
            warning_bg = "#3A2831"
            risk_bg = "#2F3148"
            title_fg = "#9FB1C9"
            value_fg = "#E9EEF7"
            warning_fg = "#FFB4BC"
        else:
            neutral_bg = "#F1F5FB"
            warning_bg = "#FFF1F2"
            risk_bg = "#F3F1FE"
            title_fg = "#66758B"
            value_fg = "#1B2430"
            warning_fg = "#B43343"

        kpis = [
            ("Outstanding", format_inr(total_outstanding, compact=True), neutral_bg, value_fg),
            ("Overdue", format_inr(total_overdue, compact=True), warning_bg, warning_fg),
            ("Delinquency", f"{overall_delinquency:.2f}%", risk_bg, value_fg),
        ]

        for index, (title, value, bg, value_color) in enumerate(kpis):
            card = tk.Frame(self.portfolio_kpi_row, bg=bg, bd=0, highlightthickness=0)
            card.pack(side="left", fill="x", expand=True, padx=(0, 6) if index < 2 else 0)

            tk.Label(card, text=title, bg=bg, fg=title_fg, font=("SF Pro Rounded", 8, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
            tk.Label(card, text=value, bg=bg, fg=value_color, font=("SF Pro Rounded", 10, "bold")).pack(anchor="w", padx=8, pady=(1, 6))

    def _tooltip_offsets(self, event, figure: Figure, tooltip_width: int, tooltip_height: int, margin: int = 14) -> tuple[int, int]:
        figure_width = figure.get_figwidth() * figure.dpi
        figure_height = figure.get_figheight() * figure.dpi
        x = event.x if event.x is not None else figure_width / 2
        y = event.y if event.y is not None else figure_height / 2

        right_space = figure_width - x
        top_space = figure_height - y

        x_offset = -margin if right_space < tooltip_width + 10 else margin
        y_offset = -margin if top_space < tooltip_height + 10 else margin
        return x_offset, y_offset

    def _build_table_row(self) -> None:
        self.table_row = tk.Frame(self.content, bg=self.PAGE_BG)
        self.table_row.pack(fill="both", expand=True)

        self.recent_card = RoundedCard(
            self.table_row,
            outer_bg=self.PAGE_BG,
            card_bg=self.CARD_BG,
            border_color=self.CARD_BORDER,
            radius=20,
        )
        self.recent_card.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.recent_header = tk.Frame(self.recent_card.content, bg=self.CARD_BG)
        self.recent_header.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(self.recent_header, text="Recent Loan Applications", bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 17, "bold")).pack(side="left")
        recent_view_all = tk.Label(self.recent_header, text="View All", bg=self.CARD_BG, fg=self.ACTION_LINK, cursor="hand2", font=("SF Pro Rounded", 10, "bold"))
        recent_view_all.pack(side="right")
        recent_view_all.bind("<Button-1>", lambda _event: self._open_recent_all_modal())

        self.recent_table_header = tk.Frame(self.recent_card.content, bg=self.TABLE_HEADER_BG)
        self.recent_table_header.pack(fill="x", padx=14)
        self._render_table_titles(
            self.recent_table_header,
            ["LOAN NUMBER", "CUSTOMER", "TYPE", "PRINCIPAL"],
            widths=[0.23, 0.33, 0.2, 0.24],
        )
        self.recent_rows_host = tk.Frame(self.recent_card.content, bg=self.CARD_BG)
        self.recent_rows_host.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.recent_rows_canvas = tk.Canvas(self.recent_rows_host, bg=self.CARD_BG, highlightthickness=0, bd=0)
        self.recent_rows_scrollbar = tk.Scrollbar(self.recent_rows_host, orient="vertical", command=self.recent_rows_canvas.yview, width=10)
        self.recent_rows_canvas.configure(yscrollcommand=self.recent_rows_scrollbar.set)
        self.recent_rows_canvas.pack(side="left", fill="both", expand=True)
        self.recent_rows_scrollbar.pack(side="right", fill="y")

        self.recent_rows = tk.Frame(self.recent_rows_canvas, bg=self.CARD_BG)
        self._recent_rows_window = self.recent_rows_canvas.create_window((0, 0), window=self.recent_rows, anchor="nw")
        self.recent_rows.bind("<Configure>", lambda _e: self.recent_rows_canvas.configure(scrollregion=self.recent_rows_canvas.bbox("all")))
        self.recent_rows_canvas.bind("<Configure>", lambda e: self.recent_rows_canvas.itemconfigure(self._recent_rows_window, width=e.width))

        self.due_card = RoundedCard(
            self.table_row,
            outer_bg=self.PAGE_BG,
            card_bg=self.CARD_BG,
            border_color=self.CARD_BORDER,
            radius=20,
        )
        self.due_card.pack(side="left", fill="both", expand=True)

        self.due_header = tk.Frame(self.due_card.content, bg=self.CARD_BG)
        self.due_header.pack(fill="x", padx=18, pady=(14, 8))
        tk.Label(self.due_header, text="Today's Due EMIs", bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 17, "bold")).pack(side="left")

        due_right = tk.Frame(self.due_header, bg=self.CARD_BG)
        due_right.pack(side="right")

        self.quick_pay = tk.Button(
            due_right,
            text="Quick Pay",
            command=self._mark_selected_due_paid,
            bg="#2366C6",
            fg="#FFFFFF",
            activebackground="#2C73DA",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("SF Pro Rounded", 9, "bold"),
            padx=10,
            pady=4,
        )
        self.quick_pay.pack(side="right", padx=(12, 0))

        due_view_all = tk.Label(due_right, text="View All", bg=self.CARD_BG, fg=self.ACTION_LINK, cursor="hand2", font=("SF Pro Rounded", 10, "bold"))
        due_view_all.pack(side="right", padx=(0, 10))
        due_view_all.bind("<Button-1>", lambda _event: self._open_due_all_modal())

        tk.Label(due_right, text=date.today().strftime("%b %d, %Y"), bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 9)).pack(side="left", padx=(0, 8))
        tk.Label(due_right, text="•", bg=self.CARD_BG, fg="#D52F3F", font=("SF Pro Rounded", 11, "bold")).pack(side="left")

        self.due_table_header = tk.Frame(self.due_card.content, bg=self.TABLE_HEADER_BG)
        self.due_table_header.pack(fill="x", padx=14)
        self._render_table_titles(
            self.due_table_header,
            ["LOAN NUMBER", "CUSTOMER", "INST #", "EMI AMOUNT"],
            widths=[0.28, 0.32, 0.14, 0.26],
        )
        self.due_rows_host = tk.Frame(self.due_card.content, bg=self.CARD_BG)
        self.due_rows_host.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.due_rows_canvas = tk.Canvas(self.due_rows_host, bg=self.CARD_BG, highlightthickness=0, bd=0)
        self.due_rows_scrollbar = tk.Scrollbar(self.due_rows_host, orient="vertical", command=self.due_rows_canvas.yview, width=10)
        self.due_rows_canvas.configure(yscrollcommand=self.due_rows_scrollbar.set)
        self.due_rows_canvas.pack(side="left", fill="both", expand=True)
        self.due_rows_scrollbar.pack(side="right", fill="y")

        self.due_rows = tk.Frame(self.due_rows_canvas, bg=self.CARD_BG)
        self._due_rows_window = self.due_rows_canvas.create_window((0, 0), window=self.due_rows, anchor="nw")
        self.due_rows.bind("<Configure>", lambda _e: self.due_rows_canvas.configure(scrollregion=self.due_rows_canvas.bbox("all")))
        self.due_rows_canvas.bind("<Configure>", lambda e: self.due_rows_canvas.itemconfigure(self._due_rows_window, width=e.width))

    def _render_table_titles(self, parent: tk.Widget, titles: list[str], widths: list[float]) -> None:
        for child in parent.winfo_children():
            child.destroy()

        parent.configure(height=38)
        parent.pack_propagate(False)
        parent.grid_rowconfigure(0, weight=1)

        for idx, title in enumerate(titles):
            weight = max(1, int((widths[idx] if idx < len(widths) else 1) * 100))
            parent.grid_columnconfigure(idx, weight=weight)
            label = tk.Label(
                parent,
                text=title,
                bg=self.TABLE_HEADER_BG,
                fg=self.TABLE_HEADER_FG,
                font=("SF Pro Rounded", 9, "bold"),
                anchor="w",
                padx=8,
                pady=9,
            )
            label.grid(row=0, column=idx, sticky="nsew")

    def refresh(self) -> None:
        metrics = LOAN_MODEL.dashboard_metrics()
        self.metric_active["value"].configure(text=str(metrics["active_count"]))
        self.metric_active["subtitle"].configure(text=format_inr(metrics["active_total"], compact=True))

        self.metric_disbursed["value"].configure(text=format_inr(metrics["disbursed_total"], compact=True))
        self.metric_disbursed["subtitle"].configure(text="")

        self.metric_overdue["value"].configure(text=str(metrics["overdue_count"]))
        self.metric_overdue["subtitle"].configure(text="")

        self.metric_collection["value"].configure(text=format_inr(metrics["monthly_collection"], compact=True))
        self.metric_collection["subtitle"].configure(text="")

        recent = LOAN_MODEL.recent_loan_applications(limit=10)
        self._render_recent_rows(recent)

        self._due_raw = LOAN_MODEL.todays_due_emis()
        self._render_due_rows(self._due_raw)

        self._render_trend_chart()
        self._render_portfolio_chart()

    def _clear_children(self, widget: tk.Widget) -> None:
        for child in widget.winfo_children():
            child.destroy()

    def _open_recent_all_modal(self) -> None:
        rows = LOAN_MODEL.recent_loan_applications(limit=500)
        modal = WaltModal(self.winfo_toplevel(), "All Recent Loan Applications", width=1020, height=560)

        if not rows:
            tk.Label(modal.content, text="No recent applications available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=8, pady=8)
        else:
            formatted = []
            for row in rows:
                formatted.append(
                    {
                        "loan_number": row.get("loan_number", "-"),
                        "customer_name": row.get("customer_name", "-"),
                        "loan_type": row.get("loan_type", "-"),
                        "principal_amount": format_inr(float(row.get("principal_amount", 0))),
                        "status": row.get("status", "-"),
                    }
                )

            table = WaltTable(
                modal.content,
                columns=[
                    ("loan_number", "Loan Number", 210),
                    ("customer_name", "Customer", 220),
                    ("loan_type", "Type", 180),
                    ("principal_amount", "Principal", 170),
                    ("status", "Status", 120),
                ],
                data=formatted,
            )
            table.pack(fill="both", expand=True)

        WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")

    def _open_due_all_modal(self) -> None:
        rows = LOAN_MODEL.todays_due_emis()
        modal = WaltModal(self.winfo_toplevel(), "All Due EMIs for Today", width=980, height=520)

        if not rows:
            tk.Label(modal.content, text="No dues for today", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=8, pady=8)
        else:
            formatted = []
            for row in rows:
                formatted.append(
                    {
                        "loan_number": row.get("loan_number", "-"),
                        "customer_name": row.get("customer_name", "-"),
                        "installment_number": row.get("installment_number", "-"),
                        "due_date": row.get("due_date", "-"),
                        "emi_amount": format_inr(float(row.get("emi_amount", 0))),
                    }
                )

            table = WaltTable(
                modal.content,
                columns=[
                    ("loan_number", "Loan Number", 220),
                    ("customer_name", "Customer", 220),
                    ("installment_number", "Inst #", 90),
                    ("due_date", "Due Date", 140),
                    ("emi_amount", "EMI", 170),
                ],
                data=formatted,
            )
            table.pack(fill="both", expand=True)

        WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")

    def _open_trend_all_modal(self) -> None:
        trend = LOAN_MODEL.disbursement_trend_last_12_months()
        labels, amounts = self._build_trend_series(trend)
        modal = WaltModal(self.winfo_toplevel(), "Loan Disbursement Trend", width=680, height=460)

        if not labels:
            tk.Label(modal.content, text="No disbursement data available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=8, pady=8)
            WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")
            return

        trend_rows = []
        total_amount = 0.0
        for month, amount in zip(labels, amounts):
            total_amount += amount
            trend_rows.append(
                {
                    "month": month,
                    "amount": format_inr(amount),
                }
            )

        tk.Label(
            modal.content,
            text=f"Total Disbursement (shown period): {format_inr(total_amount)}",
            bg=self.CARD_BG,
            fg=self.TEXT_SECONDARY,
            font=("SF Pro Rounded", 10, "bold"),
        ).pack(anchor="w", padx=8, pady=(0, 8))

        table = WaltTable(
            modal.content,
            columns=[
                ("month", "Month", 220),
                ("amount", "Disbursed Amount", 280),
            ],
            data=trend_rows,
        )
        table.pack(fill="both", expand=True)

        WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")

    def _open_portfolio_all_modal(self) -> None:
        rows = LOAN_MODEL.portfolio_management_breakdown()
        modal = WaltModal(self.winfo_toplevel(), "Loan Portfolio Breakdown", width=900, height=520)

        if not rows:
            tk.Label(modal.content, text="No portfolio data available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=8, pady=8)
            WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")
            return

        formatted = []
        for row in rows:
            outstanding = float(row.get("outstanding_principal", 0) or 0)
            overdue = float(row.get("overdue_principal", 0) or 0)
            formatted.append(
                {
                    "loan_type": row.get("loan_type", "-"),
                    "active_loans": int(row.get("active_loans", 0) or 0),
                    "outstanding": format_inr(outstanding),
                    "overdue": format_inr(overdue),
                    "delinquency": f"{float(row.get('delinquency_share', 0) or 0):.2f}%",
                }
            )

        table = WaltTable(
            modal.content,
            columns=[
                ("loan_type", "Loan Type", 230),
                ("active_loans", "Active Loans", 120),
                ("outstanding", "Outstanding", 170),
                ("overdue", "Overdue", 150),
                ("delinquency", "Delinquency", 130),
            ],
            data=formatted,
        )
        table.pack(fill="both", expand=True)

        WaltButton(modal.footer, text="Close", style="secondary", command=modal.destroy).pack(side="right")

    def _render_recent_rows(self, rows: list[dict]) -> None:
        self._clear_children(self.recent_rows)
        if not rows:
            tk.Label(self.recent_rows, text="No recent applications", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=10, pady=10)
            return

        for row in rows:
            line = tk.Frame(self.recent_rows, bg=self.CARD_BG)
            line.pack(fill="x", pady=(2, 2))

            loan_no = tk.Label(line, text=row.get("loan_number", "-"), bg=self.CARD_BG, fg=self.ACTION_LINK, font=("SF Pro Rounded", 12, "bold"), anchor="w", padx=8, pady=8)
            loan_no.pack(side="left", fill="x", expand=True)

            customer = tk.Label(line, text=row.get("customer_name", "-"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 11), anchor="w", padx=8)
            customer.pack(side="left", fill="x", expand=True)

            loan_type = tk.Label(line, text=row.get("loan_type", "-"), bg=self.CARD_BG, fg="#4E5968", font=("SF Pro Rounded", 11), anchor="w", padx=8)
            loan_type.pack(side="left", fill="x", expand=True)

            principal = tk.Label(line, text=format_inr(float(row.get("principal_amount", 0))), bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 11, "bold"), anchor="w", padx=8)
            principal.pack(side="left", fill="x", expand=True)

            tk.Frame(self.recent_rows, bg=self.ROW_DIVIDER, height=1).pack(fill="x", padx=8)

    def _render_due_rows(self, rows: list[dict]) -> None:
        self._clear_children(self.due_rows)
        self._due_row_frames = []
        self.selected_due = rows[0] if rows else None

        if not rows:
            tk.Label(self.due_rows, text="No dues for today", bg=self.CARD_BG, fg=self.TEXT_SECONDARY, font=("SF Pro Rounded", 11)).pack(anchor="w", padx=10, pady=10)
            return

        for raw in rows:
            line = tk.Frame(self.due_rows, bg=self.CARD_BG)
            line.pack(fill="x", pady=(2, 2))
            self._due_row_frames.append(line)

            loan_no = tk.Label(line, text=raw.get("loan_number", "-"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 11, "bold"), anchor="w", padx=8, pady=8)
            loan_no.pack(side="left", fill="x", expand=True)

            customer = tk.Label(line, text=raw.get("customer_name", "-"), bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 11), anchor="w", padx=8)
            customer.pack(side="left", fill="x", expand=True)

            inst = tk.Label(line, text=f"{raw.get('installment_number', '-')}", bg=self.CARD_BG, fg="#4E5968", font=("SF Pro Rounded", 11), anchor="w", padx=8)
            inst.pack(side="left", fill="x", expand=True)

            emi = tk.Label(line, text=format_inr(float(raw.get("emi_amount", 0))), bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 11, "bold"), anchor="w", padx=8)
            emi.pack(side="left", fill="x", expand=True)

            def on_click(_event, row=raw, frame=line):
                self.selected_due = row
                self._highlight_selected_due(frame)

            for widget in (line, loan_no, customer, inst, emi):
                widget.bind("<Button-1>", on_click)

            tk.Frame(self.due_rows, bg=self.ROW_DIVIDER, height=1).pack(fill="x", padx=8)

        if self._due_row_frames:
            self._highlight_selected_due(self._due_row_frames[0])

    def _highlight_selected_due(self, selected_frame: tk.Frame) -> None:
        for frame in self._due_row_frames:
            bg = self.SELECTED_ROW_BG if frame == selected_frame else self.CARD_BG
            frame.configure(bg=bg)
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=bg)

    def _mark_selected_due_paid(self) -> None:
        if not self.selected_due:
            WaltToast(self.winfo_toplevel(), "No due installment selected", "warning").show()
            return

        try:
            REPAYMENT_MODEL.record_payment(
                {
                    "loan_id": self.selected_due["loan_id"],
                    "paid_date": date.today().isoformat(),
                    "payment_mode": "UPI",
                    "payment_amount": self.selected_due["emi_amount"],
                    "transaction_reference": "DASH-QUICK-PAY",
                    "remarks": "Marked paid from dashboard quick action",
                },
                actor_user_id=self.current_user_id,
            )
            WaltToast(self.winfo_toplevel(), "EMI marked as paid", "success").show()
            self.refresh()
        except Exception as error:
            WaltToast(self.winfo_toplevel(), str(error), "danger").show()

    def _render_trend_chart(self) -> None:
        self._clear_children(self.trend_plot_holder)
        trend = LOAN_MODEL.disbursement_trend_last_12_months()

        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self.trend_plot_holder, text="matplotlib not available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=12)
            return

        if not trend:
            tk.Label(self.trend_plot_holder, text="No disbursement data available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=12)
            return

        labels, amounts = self._build_trend_series(trend)
        if not labels or all(amount <= 0 for amount in amounts):
            tk.Label(self.trend_plot_holder, text="No disbursement data available for selected period", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=12)
            return

        figure = Figure(figsize=(6.6, 3.18), dpi=100)
        axis = figure.add_subplot(111)

        active_bar = "#1682FF" if is_dark_mode() else "#0D6EFD"
        base_bar = "#133A60" if is_dark_mode() else "#CEDAE8"
        zero_bar = "#1E2E42" if is_dark_mode() else "#E7EEF5"

        bar_colors = [base_bar if amount > 0 else zero_bar for amount in amounts]
        bar_colors[-1] = active_bar

        positions = list(range(len(labels)))
        bars = axis.bar(positions, amounts, color=bar_colors, edgecolor=bar_colors, width=0.78)

        axis.set_facecolor(self.CARD_BG)
        figure.patch.set_facecolor(self.CARD_BG)
        axis.set_xlim(-0.55, len(labels) - 0.45)
        axis.set_ylim(0, max(max(amounts) * 1.25, 1.0))

        axis.set_xticks(positions)
        axis.set_xticklabels(labels)
        axis.tick_params(axis="x", labelsize=8, colors=self.AXIS_TEXT, length=0, pad=8)
        axis.tick_params(axis="y", labelleft=False, length=0)

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_visible(False)
        axis.spines["bottom"].set_color(self.AXIS_LINE)
        axis.grid(False)

        hover_annotation = axis.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "#111827", "ec": "#111827", "alpha": 0.96},
            color="#FFFFFF",
            fontsize=9,
            annotation_clip=False,
        )
        hover_annotation.set_visible(False)

        figure.subplots_adjust(left=0.03, right=0.99, top=0.97, bottom=0.22)
        canvas = FigureCanvasTkAgg(figure, master=self.trend_plot_holder)

        def on_hover(event) -> None:
            should_redraw = False
            if event.inaxes != axis or event.xdata is None or event.ydata is None:
                if hover_annotation.get_visible():
                    hover_annotation.set_visible(False)
                    canvas.draw_idle()
                return

            index = int(round(event.xdata))
            if index < 0 or index >= len(labels) or abs(event.xdata - index) > 0.48:
                if hover_annotation.get_visible():
                    hover_annotation.set_visible(False)
                    canvas.draw_idle()
                return

            hover_annotation.xy = (event.xdata, event.ydata)
            hover_annotation.set_text(f"{labels[index]}\n{format_inr(amounts[index])}")

            x_offset, y_offset = self._tooltip_offsets(event, figure, tooltip_width=150, tooltip_height=54)
            hover_annotation.set_position((x_offset, y_offset))
            hover_annotation.set_ha("right" if x_offset < 0 else "left")
            hover_annotation.set_va("top" if y_offset < 0 else "bottom")

            if not hover_annotation.get_visible():
                hover_annotation.set_visible(True)
                should_redraw = True
            else:
                should_redraw = True

            if should_redraw:
                canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_hover)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_portfolio_chart(self) -> None:
        self._clear_children(self.portfolio_plot_holder)
        self._clear_children(self.portfolio_legend_body)

        portfolio = LOAN_MODEL.portfolio_management_breakdown()
        if not MATPLOTLIB_AVAILABLE:
            tk.Label(self.portfolio_plot_holder, text="matplotlib not available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=10)
            return

        if not portfolio:
            tk.Label(self.portfolio_plot_holder, text="No portfolio data available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=10)
            return

        labels = [row["loan_type"] for row in portfolio]
        values = [float(row["outstanding_principal"]) for row in portfolio]
        active_counts = [int(row["active_loans"]) for row in portfolio]
        delinquency_shares = [float(row["delinquency_share"]) for row in portfolio]
        overdue_values = [float(row["overdue_principal"]) for row in portfolio]

        total_value = sum(values)
        total_overdue = sum(overdue_values)
        overall_delinquency = (total_overdue / total_value * 100) if total_value > 0 else 0.0
        if total_value <= 0:
            tk.Label(self.portfolio_plot_holder, text="No portfolio value available", bg=self.CARD_BG, fg=self.TEXT_SECONDARY).pack(anchor="w", pady=10)
            return

        self._render_portfolio_kpis(total_value, total_overdue, overall_delinquency)

        percentages = [(value / total_value) * 100 for value in values]
        colors = ["#1682FF", "#4B4EDC", "#B05BE4", "#33C56E", "#FFA11A", "#FF4D4F", "#6B7280"]
        palette = [colors[index % len(colors)] for index in range(len(values))]

        figure = Figure(figsize=(3.35, self._portfolio_plot_height / 104), dpi=100)
        axis = figure.add_subplot(111)
        wedges, _ = axis.pie(
            values,
            labels=None,
            startangle=90,
            counterclock=False,
            colors=palette,
            wedgeprops={"width": 0.33, "edgecolor": self.CARD_BG, "linewidth": 2},
        )

        total_active = sum(active_counts)
        axis.text(0, 0.02, format_inr(total_value, compact=True), ha="center", va="center", fontsize=11, fontweight="bold", color=self.TEXT_PRIMARY)
        axis.text(0, -0.14, f"ACTIVE {total_active}", ha="center", va="center", fontsize=8, color=self.TEXT_SECONDARY)

        hover_annotation = axis.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.35", "fc": "#111827", "ec": "#111827", "alpha": 0.95},
            color="#FFFFFF",
            fontsize=9,
            annotation_clip=False,
        )
        hover_annotation.set_visible(False)

        canvas = FigureCanvasTkAgg(figure, master=self.portfolio_plot_holder)

        def _fallback_slice_index(event) -> int | None:
            if event.xdata is None or event.ydata is None:
                return None

            radius = hypot(event.xdata, event.ydata)
            if radius < 0.35 or radius > 1.12:
                return None

            angle = (degrees(atan2(event.ydata, event.xdata)) + 360) % 360
            cursor = 90.0
            for idx, value in enumerate(values):
                span = (value / total_value) * 360.0
                end = cursor - span
                if ((cursor - angle) % 360) <= ((cursor - end) % 360):
                    return idx
                cursor = end
            return None

        def on_hover(event) -> None:
            if event.inaxes != axis:
                if hover_annotation.get_visible():
                    hover_annotation.set_visible(False)
                    canvas.draw_idle()
                return

            hover_index: int | None = None
            for idx, wedge in enumerate(wedges):
                contains, _ = wedge.contains(event)
                if contains:
                    hover_index = idx
                    break

            if hover_index is None:
                hover_index = _fallback_slice_index(event)

            if hover_index is None:
                if hover_annotation.get_visible():
                    hover_annotation.set_visible(False)
                    canvas.draw_idle()
                return

            hover_annotation.xy = (event.xdata or 0, event.ydata or 0)
            hover_annotation.set_text(
                f"{labels[hover_index]}\nOutstanding: {format_inr(values[hover_index])}\nOverdue: {format_inr(overdue_values[hover_index])}\nActive: {active_counts[hover_index]} | Delinq: {delinquency_shares[hover_index]:.1f}%"
            )

            x_offset, y_offset = self._tooltip_offsets(event, figure, tooltip_width=280, tooltip_height=112)
            hover_annotation.set_position((x_offset, y_offset))
            hover_annotation.set_ha("right" if x_offset < 0 else "left")
            hover_annotation.set_va("top" if y_offset < 0 else "bottom")

            if not hover_annotation.get_visible():
                hover_annotation.set_visible(True)
            canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", on_hover)

        axis.set_facecolor(self.CARD_BG)
        figure.patch.set_facecolor(self.CARD_BG)
        axis.set_aspect("equal")
        axis.set_xlim(-1.15, 1.15)
        axis.set_ylim(-1.1, 1.1)
        figure.tight_layout(pad=1.05)

        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        for index, label in enumerate(labels):
            row = tk.Frame(self.portfolio_legend_body, bg=self.CARD_BG)
            row.pack(fill="x", pady=3)

            line1 = tk.Frame(row, bg=self.CARD_BG)
            line1.pack(fill="x")

            dot = tk.Canvas(line1, width=10, height=10, bg=self.CARD_BG, highlightthickness=0)
            dot.pack(side="left", padx=(0, 8))
            dot.create_oval(2, 2, 8, 8, fill=palette[index], outline=palette[index])

            tk.Label(line1, text=label, bg=self.CARD_BG, fg=self.TEXT_PRIMARY, font=("SF Pro Rounded", 10)).pack(side="left")
            tk.Label(
                line1,
                text=f"{format_inr(values[index], compact=True)} ({percentages[index]:.0f}%)",
                bg=self.CARD_BG,
                fg=self.TEXT_PRIMARY,
                font=("SF Pro Rounded", 10, "bold"),
            ).pack(side="right")

            tk.Label(
                row,
                text=f"Active loans: {active_counts[index]}   Delinquency: {delinquency_shares[index]:.1f}%",
                bg=self.CARD_BG,
                fg=self.TEXT_SECONDARY,
                font=("SF Pro Rounded", 9),
            ).pack(anchor="w", padx=(18, 0), pady=(1, 0))

        self.portfolio_legend_body.update_idletasks()
        self.portfolio_legend_canvas.update_idletasks()
        content_height = self.portfolio_legend_body.winfo_reqheight()
        viewport_height = self.portfolio_legend_canvas.winfo_height()
        if content_height <= viewport_height + 2:
            self.portfolio_legend_scrollbar.pack_forget()
        elif not self.portfolio_legend_scrollbar.winfo_ismapped():
            self.portfolio_legend_scrollbar.pack(side="right", fill="y")
