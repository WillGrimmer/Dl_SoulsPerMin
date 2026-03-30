"""
Souls-per-minute calculator (run length 1–60 minutes).

Game formulas live in the constants below and in boxes_total / denizen_totals / _update.
Run: python main.py
Build exe: pyinstaller --onefile --windowed --name SoulsPerMin main.py
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# --- Trooper (souls): base + rate × minutes ---
BASE = 116.0
PER_MINUTE = 1.16

# --- Boxes: 0 for minute 1; from minute 2: base + rate × minutes ---
BOXES_BASE = 23.0
BOXES_PER_MINUTE = 2.0

# --- Denizen tiers: each is base + rate × minutes ---
DENIZEN_T1_BASE = 41.0
DENIZEN_T1_PER = 0.44
DENIZEN_T2_BASE = 68.0
DENIZEN_T2_PER = 0.73
DENIZEN_T3_BASE = 181.0
DENIZEN_T3_PER = 1.95

# Share multipliers
TWO_PERSON_SHARE_OF_WAVE = 0.54
THREE_PERSON_SHARE_OF_WAVE = 0.36
METRIC_OPTIONS = [
    ("None", "None"),
    ("Trooper", "Trooper"),
    ("Wave", "Wave"),
    ("2 person share", "2 person share"),
    ("3 person share", "3 person share"),
    ("Boxes", "Boxes"),
    ("Box Run", "Box Run"),
    ("Tier 1 Denizen", "Tier 1 Denizen"),
    ("Tier 2 Denizen", "Tier 2 Denizen"),
    ("Tier 3 Denizen", "Tier 3 Denizen"),
    ("2 min camp", "2 min camp"),
    ("medium camp", "medium camp"),
    ("church", "church"),
    ("combo", "combo"),
    ("Tripple", "Tripple"),
]


def boxes_total(minutes: int) -> float:
    """Boxes score: 0 before 2 minutes; from 2 minutes onward: 23 + 2 per minute."""
    if minutes < 2:
        return 0.0
    return BOXES_BASE + BOXES_PER_MINUTE * minutes


def denizen_totals(minutes: int) -> tuple[float, float, float]:
    """Tier 1–3 denizen values for the given run length (minutes)."""
    t1 = DENIZEN_T1_BASE + DENIZEN_T1_PER * minutes
    t2 = DENIZEN_T2_BASE + DENIZEN_T2_PER * minutes
    t3 = DENIZEN_T3_BASE + DENIZEN_T3_PER * minutes
    return t1, t2, t3


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        # Vertical order: results at top; minutes slider + spin box at bottom (inside scroll area).
        self.setWindowTitle("Souls per minute")
        self.setMinimumWidth(800)
        self.setMinimumHeight(360)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 12, 14, 14)

        title = QLabel("Minutes (1–60)")
        title.setObjectName("title")

        # Minutes: spin box and slider stay in sync; both drive _update via slider.valueChanged.
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(1, 60)
        self.minute_spin.setSuffix(" min")
        self.minute_spin.setObjectName("minuteSpin")
        self.minute_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.minute_spin.setKeyboardTracking(True)
        self.minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(60)
        self.slider.setSingleStep(1)
        self.slider.setPageStep(1)
        self.slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.slider.setTracking(True)
        self.slider.setObjectName("minuteSlider")
        self.slider.setMaximumHeight(20)
        self.slider.valueChanged.connect(self._update)
        self.minute_spin.valueChanged.connect(self.slider.setValue)
        self.round_toggle = QCheckBox("Round results")
        self.round_toggle.setObjectName("roundToggle")
        self.round_toggle.toggled.connect(lambda _: self._update(self.slider.value()))
        self.compare_enabled = QCheckBox("Enable Side A / Side B comparison")
        self.compare_enabled.setObjectName("roundToggle")
        self.compare_enabled.setChecked(True)
        self.compare_enabled.toggled.connect(lambda _: self._update(self.slider.value()))
        self.scan_mode_toggle = QCheckBox("Scan range mode")
        self.scan_mode_toggle.setObjectName("roundToggle")
        self.scan_mode_toggle.toggled.connect(lambda _: self._update(self.slider.value()))

        row = QHBoxLayout()
        self.min_label = QLabel("1")
        self.min_label.setMinimumWidth(28)
        self.max_label = QLabel("60")
        self.max_label.setMinimumWidth(28)
        self.max_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(self.min_label)
        row.addWidget(self.slider, stretch=1)
        row.addWidget(self.max_label)

        # Row 1: Trooper | Wave | 2 person share | 3 person share
        trooper_label = QLabel("Trooper")
        trooper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trooper_label.setObjectName("title")

        self.result_value = QLabel()
        self.result_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_value.setObjectName("valueLabel")

        self.detail_label = QLabel()
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        self.detail_label.setObjectName("formula")

        wave_label = QLabel("Wave")
        wave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wave_label.setObjectName("title")
        self.wave_value = QLabel()
        self.wave_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wave_value.setObjectName("valueLabelWave")
        self.wave_detail = QLabel()
        self.wave_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wave_detail.setObjectName("formula")

        share_label = QLabel("2 person share")
        share_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        share_label.setObjectName("title")
        share_label.setWordWrap(True)
        self.share_value = QLabel()
        self.share_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share_value.setObjectName("valueLabelShare")
        self.share_detail = QLabel()
        self.share_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share_detail.setObjectName("formula")

        share3_label = QLabel("3 person share")
        share3_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        share3_label.setObjectName("title")
        share3_label.setWordWrap(True)
        self.share3_value = QLabel()
        self.share3_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share3_value.setObjectName("valueLabelShare3")
        self.share3_detail = QLabel()
        self.share3_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.share3_detail.setObjectName("formula")

        boxes_label = QLabel("Boxes")
        boxes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boxes_label.setObjectName("title")

        self.boxes_value = QLabel()
        self.boxes_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boxes_value.setObjectName("valueLabelBoxes")

        self.boxes_detail = QLabel()
        self.boxes_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boxes_detail.setWordWrap(True)
        self.boxes_detail.setObjectName("formula")

        boxrun_label = QLabel("Box Run")
        boxrun_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boxrun_label.setObjectName("title")
        self.boxrun_value = QLabel()
        self.boxrun_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boxrun_value.setObjectName("valueLabelBoxRun")
        self.boxrun_detail = QLabel()
        self.boxrun_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boxrun_detail.setObjectName("formula")

        def _hline() -> QFrame:
            # Thin rule between big number and formula line in each column.
            s = QFrame()
            s.setFrameShape(QFrame.Shape.HLine)
            s.setFrameShadow(QFrame.Shadow.Sunken)
            s.setFixedHeight(1)
            return s

        trooper_wave_strip = QWidget()
        tw = QHBoxLayout(trooper_wave_strip)
        tw.setSpacing(8)
        trooper_col = QVBoxLayout()
        trooper_col.setSpacing(2)
        trooper_col.addWidget(trooper_label)
        trooper_col.addWidget(self.result_value)
        trooper_col.addWidget(_hline())
        trooper_col.addWidget(self.detail_label)
        wave_col = QVBoxLayout()
        wave_col.setSpacing(2)
        wave_col.addWidget(wave_label)
        wave_col.addWidget(self.wave_value)
        wave_col.addWidget(_hline())
        wave_col.addWidget(self.wave_detail)
        share_col = QVBoxLayout()
        share_col.setSpacing(2)
        share_col.addWidget(share_label)
        share_col.addWidget(self.share_value)
        share_col.addWidget(_hline())
        share_col.addWidget(self.share_detail)
        share3_col = QVBoxLayout()
        share3_col.setSpacing(2)
        share3_col.addWidget(share3_label)
        share3_col.addWidget(self.share3_value)
        share3_col.addWidget(_hline())
        share3_col.addWidget(self.share3_detail)
        tw.addLayout(trooper_col, 1)
        tw.addLayout(wave_col, 1)
        tw.addLayout(share_col, 1)
        tw.addLayout(share3_col, 1)

        boxes_boxrun_strip = QWidget()
        bb = QHBoxLayout(boxes_boxrun_strip)
        bb.setSpacing(8)
        boxes_col = QVBoxLayout()
        boxes_col.setSpacing(2)
        boxes_col.addWidget(boxes_label)
        boxes_col.addWidget(self.boxes_value)
        boxes_col.addWidget(_hline())
        boxes_col.addWidget(self.boxes_detail)
        boxrun_col = QVBoxLayout()
        boxrun_col.setSpacing(2)
        boxrun_col.addWidget(boxrun_label)
        boxrun_col.addWidget(self.boxrun_value)
        boxrun_col.addWidget(_hline())
        boxrun_col.addWidget(self.boxrun_detail)
        bb.addLayout(boxes_col, 1)
        bb.addLayout(boxrun_col, 1)

        # Row 2: Boxes | Box Run — then denizen tiers, then camp composites.
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sep2.setFixedHeight(1)

        d1_label = QLabel("Tier 1 Denizen")
        d1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d1_label.setObjectName("title")
        d1_label.setWordWrap(True)
        self.denizen_t1_value = QLabel()
        self.denizen_t1_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t1_value.setObjectName("valueLabelD1")
        self.denizen_t1_detail = QLabel()
        self.denizen_t1_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t1_detail.setWordWrap(True)
        self.denizen_t1_detail.setObjectName("formula")

        d2_label = QLabel("Tier 2 Denizen")
        d2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d2_label.setObjectName("title")
        d2_label.setWordWrap(True)
        self.denizen_t2_value = QLabel()
        self.denizen_t2_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t2_value.setObjectName("valueLabelD2")
        self.denizen_t2_detail = QLabel()
        self.denizen_t2_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t2_detail.setWordWrap(True)
        self.denizen_t2_detail.setObjectName("formula")

        d3_label = QLabel("Tier 3 Denizen")
        d3_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d3_label.setObjectName("title")
        d3_label.setWordWrap(True)
        self.denizen_t3_value = QLabel()
        self.denizen_t3_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t3_value.setObjectName("valueLabelD3")
        self.denizen_t3_detail = QLabel()
        self.denizen_t3_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.denizen_t3_detail.setWordWrap(True)
        self.denizen_t3_detail.setObjectName("formula")

        layout.addWidget(trooper_wave_strip)
        layout.addWidget(boxes_boxrun_strip)
        layout.addWidget(sep2)

        denizen_strip = QWidget()
        denizen_strip.setObjectName("denizenStrip")
        denizen_row = QHBoxLayout(denizen_strip)
        denizen_row.setSpacing(6)
        denizen_row.setContentsMargins(0, 0, 0, 0)

        col1 = QVBoxLayout()
        col1.setSpacing(2)
        col1.addWidget(d1_label)
        col1.addWidget(self.denizen_t1_value)
        col1.addWidget(self.denizen_t1_detail)

        col2 = QVBoxLayout()
        col2.setSpacing(2)
        col2.addWidget(d2_label)
        col2.addWidget(self.denizen_t2_value)
        col2.addWidget(self.denizen_t2_detail)

        col3 = QVBoxLayout()
        col3.setSpacing(2)
        col3.addWidget(d3_label)
        col3.addWidget(self.denizen_t3_value)
        col3.addWidget(self.denizen_t3_detail)

        denizen_row.addLayout(col1, 1)
        denizen_row.addLayout(col2, 1)
        denizen_row.addLayout(col3, 1)

        layout.addWidget(denizen_strip)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setFrameShadow(QFrame.Shadow.Sunken)
        sep3.setFixedHeight(1)
        layout.addWidget(sep3)

        camp_strip = QWidget()
        camp_strip.setObjectName("campStrip")
        camp_row = QHBoxLayout(camp_strip)
        camp_row.setSpacing(4)
        camp_row.setContentsMargins(0, 0, 0, 0)

        def _camp_column(title: str, value_name: str) -> tuple[QLabel, QLabel]:
            """One camp column: title, value (objectName for QSS color), formula."""
            lab = QLabel(title)
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lab.setObjectName("title")
            lab.setWordWrap(True)
            val = QLabel()
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setObjectName(value_name)
            det = QLabel()
            det.setAlignment(Qt.AlignmentFlag.AlignCenter)
            det.setWordWrap(True)
            det.setObjectName("formula")
            c = QVBoxLayout()
            c.setSpacing(2)
            c.addWidget(lab)
            c.addWidget(val)
            c.addWidget(det)
            camp_row.addLayout(c, 1)
            return val, det

        self.camp_twomin_value, self.camp_twomin_detail = _camp_column(
            "2 min camp", "valueLabelC1"
        )
        self.camp_medium_value, self.camp_medium_detail = _camp_column(
            "medium camp", "valueLabelC2"
        )
        self.camp_church_value, self.camp_church_detail = _camp_column(
            "church", "valueLabelC3"
        )
        self.camp_combo_value, self.camp_combo_detail = _camp_column(
            "combo", "valueLabelC4"
        )
        self.camp_tripple_value, self.camp_tripple_detail = _camp_column(
            "Tripple", "valueLabelC5"
        )

        layout.addWidget(camp_strip)
        self.compare_section = QWidget()
        compare_layout = QVBoxLayout(self.compare_section)
        compare_layout.setSpacing(6)
        compare_layout.setContentsMargins(14, 12, 14, 14)

        compare_title = QLabel("Comparison")
        compare_title.setObjectName("title")
        compare_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(compare_title)

        # The comparison tab controls are mirrored to the calculator's minute
        # (so both tabs always use the same run length n).
        compare_minute_title = QLabel("Minutes (1–60)")
        compare_minute_title.setObjectName("title")
        compare_minute_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(compare_minute_title)

        self.compare_minute_spin = QSpinBox()
        self.compare_minute_spin.setRange(1, 60)
        self.compare_minute_spin.setSuffix(" min")
        self.compare_minute_spin.setObjectName("minuteSpin")
        self.compare_minute_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_minute_spin.setKeyboardTracking(True)
        self.compare_minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        # Spin box edits update the shared minute state (calculator + scan).
        self.compare_minute_spin.valueChanged.connect(self.slider.setValue)

        compare_spin_row = QHBoxLayout()
        compare_spin_row.addStretch(1)
        compare_spin_row.addWidget(self.compare_minute_spin)
        compare_spin_row.addStretch(1)
        compare_layout.addLayout(compare_spin_row)

        self.compare_slider = QSlider(Qt.Orientation.Horizontal)
        self.compare_slider.setMinimum(1)
        self.compare_slider.setMaximum(60)
        self.compare_slider.setSingleStep(1)
        self.compare_slider.setPageStep(1)
        self.compare_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.compare_slider.setTracking(True)
        self.compare_slider.setObjectName("minuteSlider")
        self.compare_slider.setMaximumHeight(20)
        # Slider edits update the shared minute state (calculator + scan).
        self.compare_slider.valueChanged.connect(self.slider.setValue)

        compare_slider_row = QHBoxLayout()
        compare_slider_min = QLabel("1")
        compare_slider_min.setMinimumWidth(28)
        compare_slider_max = QLabel("60")
        compare_slider_max.setMinimumWidth(28)
        compare_slider_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        compare_slider_row.addWidget(compare_slider_min)
        compare_slider_row.addWidget(self.compare_slider, stretch=1)
        compare_slider_row.addWidget(compare_slider_max)
        compare_layout.addLayout(compare_slider_row)

        compare_toggle_row = QHBoxLayout()
        compare_toggle_row.addStretch(1)
        compare_toggle_row.addWidget(self.compare_enabled)
        compare_toggle_row.addSpacing(8)
        compare_toggle_row.addWidget(self.scan_mode_toggle)
        compare_toggle_row.addStretch(1)
        compare_layout.addLayout(compare_toggle_row)

        compare_sides = QHBoxLayout()
        compare_sides.setSpacing(8)
        side_a_box = QVBoxLayout()
        side_b_box = QVBoxLayout()
        side_a_label = QLabel("Side A")
        side_b_label = QLabel("Side B")
        side_a_label.setObjectName("title")
        side_b_label.setObjectName("title")
        side_a_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_b_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_a_box.addWidget(side_a_label)
        side_b_box.addWidget(side_b_label)

        self.side_a_rows: list[tuple[QComboBox, QDoubleSpinBox]] = []
        self.side_b_rows: list[tuple[QComboBox, QDoubleSpinBox]] = []

        def _add_compare_row(target: list[tuple[QComboBox, QDoubleSpinBox]], box: QVBoxLayout) -> None:
            r = QHBoxLayout()
            metric = QComboBox()
            metric.setObjectName("metricPicker")
            metric.addItems([label for _, label in METRIC_OPTIONS])
            mult = QDoubleSpinBox()
            mult.setRange(0.0, 999.0)
            mult.setDecimals(2)
            mult.setSingleStep(0.25)
            mult.setValue(1.0)
            mult.setPrefix("x ")
            mult.setObjectName("multSpin")
            metric.currentIndexChanged.connect(lambda _: self._update(self.slider.value()))
            mult.valueChanged.connect(lambda _: self._update(self.slider.value()))
            r.addWidget(metric, 3)
            r.addWidget(mult, 2)
            box.addLayout(r)
            target.append((metric, mult))

        for _ in range(3):
            _add_compare_row(self.side_a_rows, side_a_box)
            _add_compare_row(self.side_b_rows, side_b_box)

        compare_sides.addLayout(side_a_box, 1)
        compare_sides.addLayout(side_b_box, 1)
        compare_layout.addLayout(compare_sides)

        self.scan_from_spin = QSpinBox()
        self.scan_from_spin.setRange(1, 60)
        self.scan_from_spin.setValue(1)
        self.scan_from_spin.setPrefix("From ")
        self.scan_from_spin.setSuffix("m")
        self.scan_to_spin = QSpinBox()
        self.scan_to_spin.setRange(1, 60)
        self.scan_to_spin.setValue(60)
        self.scan_to_spin.setPrefix("To ")
        self.scan_to_spin.setSuffix("m")
        self.scan_from_spin.valueChanged.connect(lambda _: self._update(self.slider.value()))
        self.scan_to_spin.valueChanged.connect(lambda _: self._update(self.slider.value()))
        scan_row = QHBoxLayout()
        scan_row.addStretch(1)
        scan_row.addWidget(self.scan_from_spin)
        scan_row.addWidget(self.scan_to_spin)
        scan_row.addStretch(1)
        compare_layout.addLayout(scan_row)

        self.compare_result = QLabel()
        self.compare_result.setObjectName("title")
        self.compare_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_detail = QLabel()
        self.compare_detail.setObjectName("formula")
        self.compare_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_detail.setWordWrap(True)
        self.scan_result = QLabel()
        self.scan_result.setObjectName("formula")
        self.scan_result.setWordWrap(True)
        self.scan_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compare_layout.addWidget(self.compare_result)
        compare_layout.addWidget(self.compare_detail)
        compare_layout.addWidget(self.scan_result)

        self.urn_section = QWidget()
        urn_layout = QVBoxLayout(self.urn_section)
        urn_layout.setSpacing(6)
        urn_layout.setContentsMargins(14, 12, 14, 14)

        urn_title = QLabel("Urns")
        urn_title.setObjectName("title")
        urn_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        urn_layout.addWidget(urn_title)

        urn_minute_title = QLabel("Minutes (1–60)")
        urn_minute_title.setObjectName("title")
        urn_minute_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        urn_layout.addWidget(urn_minute_title)

        self.urn_minute_spin = QSpinBox()
        self.urn_minute_spin.setRange(1, 60)
        self.urn_minute_spin.setSuffix(" min")
        self.urn_minute_spin.setObjectName("minuteSpin")
        self.urn_minute_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.urn_minute_spin.valueChanged.connect(self.slider.setValue)
        urn_spin_row = QHBoxLayout()
        urn_spin_row.addStretch(1)
        urn_spin_row.addWidget(self.urn_minute_spin)
        urn_spin_row.addStretch(1)
        urn_layout.addLayout(urn_spin_row)

        self.urn_minute_slider = QSlider(Qt.Orientation.Horizontal)
        self.urn_minute_slider.setMinimum(1)
        self.urn_minute_slider.setMaximum(60)
        self.urn_minute_slider.setSingleStep(1)
        self.urn_minute_slider.setPageStep(1)
        self.urn_minute_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.urn_minute_slider.setTracking(True)
        self.urn_minute_slider.setObjectName("minuteSlider")
        self.urn_minute_slider.setMaximumHeight(20)
        self.urn_minute_slider.valueChanged.connect(self.slider.setValue)
        urn_slider_row = QHBoxLayout()
        urn_slider_min = QLabel("1")
        urn_slider_min.setMinimumWidth(28)
        urn_slider_max = QLabel("60")
        urn_slider_max.setMinimumWidth(28)
        urn_slider_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        urn_slider_row.addWidget(urn_slider_min)
        urn_slider_row.addWidget(self.urn_minute_slider, stretch=1)
        urn_slider_row.addWidget(urn_slider_max)
        urn_layout.addLayout(urn_slider_row)

        deficit_title = QLabel("Deficit (0% - 50%)")
        deficit_title.setObjectName("title")
        deficit_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        urn_layout.addWidget(deficit_title)
        self.deficit_slider = QSlider(Qt.Orientation.Horizontal)
        self.deficit_slider.setMinimum(0)
        self.deficit_slider.setMaximum(50)
        self.deficit_slider.setSingleStep(1)
        self.deficit_slider.setPageStep(1)
        self.deficit_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.deficit_slider.setTracking(True)
        self.deficit_slider.setObjectName("minuteSlider")
        self.deficit_slider.setMaximumHeight(20)
        self.deficit_slider.valueChanged.connect(lambda _: self._update(self.slider.value()))
        deficit_row = QHBoxLayout()
        deficit_min = QLabel("0%")
        deficit_min.setMinimumWidth(28)
        deficit_max = QLabel("50%")
        deficit_max.setMinimumWidth(28)
        deficit_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        deficit_row.addWidget(deficit_min)
        deficit_row.addWidget(self.deficit_slider, stretch=1)
        deficit_row.addWidget(deficit_max)
        urn_layout.addLayout(deficit_row)
        self.deficit_value_label = QLabel("Deficit: 0%")
        self.deficit_value_label.setObjectName("formula")
        self.deficit_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        urn_layout.addWidget(self.deficit_value_label)

        urn_value_title = QLabel("Urn Value")
        urn_value_title.setObjectName("title")
        urn_value_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.urn_value_label = QLabel()
        self.urn_value_label.setObjectName("valueLabel")
        self.urn_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.urn_formula_label = QLabel("1300 + 230/min (updates every 5 min from 10m)")
        self.urn_formula_label.setObjectName("formula")
        self.urn_formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.urn_formula_label.setWordWrap(True)
        urn_layout.addWidget(urn_value_title)
        urn_layout.addWidget(self.urn_value_label)
        urn_layout.addWidget(self.urn_formula_label)

        comeback_title = QLabel("Comeback Value")
        comeback_title.setObjectName("title")
        comeback_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.comeback_value_label = QLabel()
        self.comeback_value_label.setObjectName("valueLabelWave")
        self.comeback_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.comeback_formula_label = QLabel()
        self.comeback_formula_label.setObjectName("formula")
        self.comeback_formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.comeback_formula_label.setWordWrap(True)
        urn_layout.addWidget(comeback_title)
        urn_layout.addWidget(self.comeback_value_label)
        urn_layout.addWidget(self.comeback_formula_label)

        # Minutes control dock (also listed last so it sits at the bottom of the scroll view).
        layout.addWidget(_hline())
        layout.addWidget(title)
        spin_row = QHBoxLayout()
        spin_row.addStretch(1)
        spin_row.addWidget(self.minute_spin)
        spin_row.addStretch(1)
        layout.addLayout(spin_row)
        round_row = QHBoxLayout()
        round_row.addStretch(1)
        round_row.addWidget(self.round_toggle)
        round_row.addStretch(1)
        layout.addLayout(round_row)
        layout.addLayout(row)

        calc_scroll = QScrollArea()
        calc_scroll.setWidgetResizable(True)
        calc_scroll.setFrameShape(QFrame.Shape.NoFrame)
        calc_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        calc_scroll.setWidget(central)

        compare_scroll = QScrollArea()
        compare_scroll.setWidgetResizable(True)
        compare_scroll.setFrameShape(QFrame.Shape.NoFrame)
        compare_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        compare_scroll.setWidget(self.compare_section)

        urn_scroll = QScrollArea()
        urn_scroll.setWidgetResizable(True)
        urn_scroll.setFrameShape(QFrame.Shape.NoFrame)
        urn_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        urn_scroll.setWidget(self.urn_section)

        self.tabs = QTabWidget()
        self.tabs.addTab(calc_scroll, "Calculator")
        self.tabs.addTab(compare_scroll, "Comparison")
        self.tabs.addTab(urn_scroll, "Urns")
        self.setCentralWidget(self.tabs)
        self.resize(1040, 640)

        navigate_menu = self.menuBar().addMenu("Navigate")
        self.goto_calc_action = QAction("Calculator", self)
        self.goto_compare_action = QAction("Comparison", self)
        self.goto_urn_action = QAction("Urns", self)
        self.goto_calc_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        self.goto_compare_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        self.goto_urn_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        navigate_menu.addAction(self.goto_calc_action)
        navigate_menu.addAction(self.goto_compare_action)
        navigate_menu.addAction(self.goto_urn_action)

        self._apply_style()
        # Avoid firing valueChanged twice on startup (slider + explicit _update).
        self.slider.blockSignals(True)
        self.slider.setValue(1)
        self.slider.blockSignals(False)
        self._update(1)

    def _apply_style(self) -> None:
        # Object names (#title, #valueLabel, #denizenStrip, …) are referenced here.
        self.setStyleSheet(
            """
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 12px; }
            QLabel#title { font-size: 14px; font-weight: 600; color: #cba6f7; }
            QLabel#formula {
                font-size: 12px;
                color: #a6adc8;
                padding: 0px;
            }
            QSpinBox#minuteSpin {
                background-color: #313244;
                color: #89b4fa;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 18px;
                font-weight: 700;
                min-width: 5.5em;
            }
            QSpinBox#minuteSpin:focus {
                border: 1px solid #89b4fa;
            }
            QSpinBox#minuteSpin::up-button, QSpinBox#minuteSpin::down-button {
                width: 18px;
                border: none;
                background: #45475a;
            }
            QSpinBox#minuteSpin::up-button:hover, QSpinBox#minuteSpin::down-button:hover {
                background: #585b70;
            }
            QComboBox#metricPicker, QDoubleSpinBox#multSpin {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 3px 6px;
            }
            QCheckBox#roundToggle {
                color: #cdd6f4;
                spacing: 6px;
                padding: 2px 0;
            }
            QCheckBox#roundToggle::indicator {
                width: 14px;
                height: 14px;
            }
            QLabel#valueLabel {
                font-size: 38px;
                font-weight: 700;
                color: #a6e3a1;
                padding: 4px 4px;
            }
            QLabel#valueLabelBoxes {
                font-size: 38px;
                font-weight: 700;
                color: #f9e2af;
                padding: 4px 4px;
            }
            QLabel#valueLabelWave {
                font-size: 38px;
                font-weight: 700;
                color: #74c7ec;
                padding: 4px 4px;
            }
            QLabel#valueLabelShare {
                font-size: 38px;
                font-weight: 700;
                color: #cba6f7;
                padding: 4px 4px;
            }
            QLabel#valueLabelShare3 {
                font-size: 38px;
                font-weight: 700;
                color: #f2cdcd;
                padding: 4px 4px;
            }
            QLabel#valueLabelBoxRun {
                font-size: 38px;
                font-weight: 700;
                color: #f5c2e7;
                padding: 4px 4px;
            }
            QLabel#valueLabelD1 {
                font-size: 38px;
                font-weight: 700;
                color: #94e2d5;
                padding: 4px 4px;
            }
            QLabel#valueLabelD2 {
                font-size: 38px;
                font-weight: 700;
                color: #89b4fa;
                padding: 4px 4px;
            }
            QLabel#valueLabelD3 {
                font-size: 38px;
                font-weight: 700;
                color: #f5c2e7;
                padding: 4px 4px;
            }
            QWidget#denizenStrip QLabel#valueLabelD1,
            QWidget#denizenStrip QLabel#valueLabelD2,
            QWidget#denizenStrip QLabel#valueLabelD3 {
                font-size: 30px;
                padding: 2px 2px;
            }
            QWidget#denizenStrip QLabel#title {
                font-size: 12px;
            }
            QWidget#campStrip QLabel#valueLabelC1,
            QWidget#campStrip QLabel#valueLabelC2,
            QWidget#campStrip QLabel#valueLabelC3,
            QWidget#campStrip QLabel#valueLabelC4,
            QWidget#campStrip QLabel#valueLabelC5 {
                font-size: 24px;
                font-weight: 700;
                padding: 2px 1px;
            }
            QWidget#campStrip QLabel#valueLabelC1 { color: #f38ba8; }
            QWidget#campStrip QLabel#valueLabelC2 { color: #fab387; }
            QWidget#campStrip QLabel#valueLabelC3 { color: #a6e3a1; }
            QWidget#campStrip QLabel#valueLabelC4 { color: #89dceb; }
            QWidget#campStrip QLabel#valueLabelC5 { color: #b4befe; }
            QWidget#campStrip QLabel#title {
                font-size: 11px;
            }
            QWidget#campStrip QLabel#formula {
                font-size: 11px;
            }
            QSlider#minuteSlider {
                min-height: 16px;
                max-height: 20px;
            }
            QSlider#minuteSlider::groove:horizontal {
                height: 3px;
                background: #45475a;
                border-radius: 2px;
            }
            QSlider#minuteSlider::handle:horizontal {
                background: #89b4fa;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QSlider#minuteSlider::sub-page:horizontal {
                background: #89b4fa;
                border-radius: 2px;
            }
            """
        )

    def _update(self, minutes: int) -> None:
        # Mirror slider → spin box without re-entering setValue on the slider (feedback loop).
        self.minute_spin.blockSignals(True)
        self.minute_spin.setValue(minutes)
        self.minute_spin.blockSignals(False)
        # Keep the comparison-tab minute controls in sync with the main calculator.
        self.compare_minute_spin.blockSignals(True)
        self.compare_minute_spin.setValue(minutes)
        self.compare_minute_spin.blockSignals(False)
        self.compare_slider.blockSignals(True)
        self.compare_slider.setValue(minutes)
        self.compare_slider.blockSignals(False)
        self.urn_minute_spin.blockSignals(True)
        self.urn_minute_spin.setValue(minutes)
        self.urn_minute_spin.blockSignals(False)
        self.urn_minute_slider.blockSignals(True)
        self.urn_minute_slider.setValue(minutes)
        self.urn_minute_slider.blockSignals(False)

        def fmt(value: float) -> str:
            if self.round_toggle.isChecked():
                return str(int(round(value)))
            return f"{value:g}"

        metrics = self._metrics_for(minutes)

        # Trooper, Wave (×4 Trooper), 2 person share (×0.54 Wave), 3 person share (×0.36 Wave)
        self.result_value.setText(fmt(metrics["Trooper"]))
        self.detail_label.setText(f"116 + (1.16 × {minutes})")
        self.wave_value.setText(fmt(metrics["Wave"]))
        self.wave_detail.setText("Trooper × 4")
        self.share_value.setText(fmt(metrics["2 person share"]))
        self.share_detail.setText("Wave × 0.54")
        self.share3_value.setText(fmt(metrics["3 person share"]))
        self.share3_detail.setText("Wave × 0.36")

        boxes = metrics["Boxes"]
        self.boxes_value.setText(fmt(boxes))
        if minutes < 2:
            self.boxes_detail.setText("0 (before 2 min)")
        else:
            self.boxes_detail.setText(f"23 + (2 × {minutes})")
        self.boxrun_value.setText(fmt(metrics["Box Run"]))
        self.boxrun_detail.setText("Boxes × 4")

        # Denizen tiers, then camp rows (linear combos of t1–t3)
        t1 = metrics["Tier 1 Denizen"]
        t2 = metrics["Tier 2 Denizen"]
        t3 = metrics["Tier 3 Denizen"]
        self.denizen_t1_value.setText(fmt(t1))
        self.denizen_t1_detail.setText(f"41 + (0.44 × {minutes})")
        self.denizen_t2_value.setText(fmt(t2))
        self.denizen_t2_detail.setText(f"68 + (0.73 × {minutes})")
        self.denizen_t3_value.setText(fmt(t3))
        self.denizen_t3_detail.setText(f"181 + (1.95 × {minutes})")

        self.camp_twomin_value.setText(fmt(t1 * 3))
        self.camp_twomin_detail.setText("3 × Tier 1")
        self.camp_medium_value.setText(fmt(t2 * 3))
        self.camp_medium_detail.setText("3 × Tier 2")
        self.camp_church_value.setText(fmt(t1 * 4 + t2))
        self.camp_church_detail.setText("4 × Tier 1 + Tier 2")
        self.camp_combo_value.setText(fmt(t2 * 2 + t3))
        self.camp_combo_detail.setText("2 × Tier 2 + Tier 3")
        self.camp_tripple_value.setText(fmt(t3 * 3))
        self.camp_tripple_detail.setText("3 × Tier 3")

        if self.compare_enabled.isChecked():
            side_a = self._basket_total(self.side_a_rows, metrics)
            side_b = self._basket_total(self.side_b_rows, metrics)
            diff = side_a - side_b
            winner = "Tie"
            if diff > 0:
                winner = "Side A"
            elif diff < 0:
                winner = "Side B"
            self.compare_result.setText(
                f"Side A {fmt(side_a)}  vs  Side B {fmt(side_b)}  ->  {winner}"
            )
            self.compare_detail.setText(f"Difference: {fmt(abs(diff))}")
            if self.scan_mode_toggle.isChecked():
                start = min(self.scan_from_spin.value(), self.scan_to_spin.value())
                end = max(self.scan_from_spin.value(), self.scan_to_spin.value())
                self.scan_result.setText(self._scan_ranges(start, end))
            else:
                self.scan_result.setText("")
        else:
            self.compare_result.setText("Comparison disabled")
            self.compare_detail.setText("")
            self.scan_result.setText("")

        # Urns tab: deficit applies to comeback bonus as a percentage multiplier.
        deficit_percent = self.deficit_slider.value()
        deficit_ratio = deficit_percent / 100.0
        self.deficit_value_label.setText(f"Deficit: {deficit_percent}%")
        # Urn value only advances on 5-minute checkpoints, starting at 10 minutes.
        urn_minute = 0 if minutes < 10 else (minutes // 5) * 5
        urn_value = 1300 + 230 * urn_minute
        comeback_value = urn_value + 130 * minutes * deficit_ratio
        self.urn_value_label.setText(fmt(urn_value))
        self.comeback_value_label.setText(fmt(comeback_value))
        self.comeback_formula_label.setText(
            f"{fmt(urn_value)} + (130 × {minutes} × {deficit_percent}%)"
        )

    def _metrics_for(self, minutes: int) -> dict[str, float]:
        total = BASE + PER_MINUTE * minutes
        wave = total * 4
        boxes = boxes_total(minutes)
        t1, t2, t3 = denizen_totals(minutes)
        return {
            "None": 0.0,
            "Trooper": total,
            "Wave": wave,
            "2 person share": wave * TWO_PERSON_SHARE_OF_WAVE,
            "3 person share": wave * THREE_PERSON_SHARE_OF_WAVE,
            "Boxes": boxes,
            "Box Run": boxes * 4,
            "Tier 1 Denizen": t1,
            "Tier 2 Denizen": t2,
            "Tier 3 Denizen": t3,
            "2 min camp": t1 * 3,
            "medium camp": t2 * 3,
            "church": t1 * 4 + t2,
            "combo": t2 * 2 + t3,
            "Tripple": t3 * 3,
        }

    def _basket_total(
        self, rows: list[tuple[QComboBox, QDoubleSpinBox]], metrics: dict[str, float]
    ) -> float:
        total = 0.0
        for metric_box, mult_box in rows:
            metric = metric_box.currentText()
            total += metrics.get(metric, 0.0) * mult_box.value()
        return total

    def _scan_ranges(self, start: int, end: int) -> str:
        winners: list[tuple[int, str]] = []
        for minute in range(start, end + 1):
            metrics = self._metrics_for(minute)
            side_a = self._basket_total(self.side_a_rows, metrics)
            side_b = self._basket_total(self.side_b_rows, metrics)
            diff = side_a - side_b
            winner = "Tie"
            if diff > 1e-9:
                winner = "A"
            elif diff < -1e-9:
                winner = "B"
            winners.append((minute, winner))

        if not winners:
            return ""

        segments: list[str] = []
        seg_start, seg_winner = winners[0]
        prev_minute = seg_start
        breakpoints: list[int] = []
        for minute, winner in winners[1:]:
            if winner != seg_winner:
                if seg_start == prev_minute:
                    segments.append(f"{seg_start}: {seg_winner}")
                else:
                    segments.append(f"{seg_start}-{prev_minute}: {seg_winner}")
                breakpoints.append(minute)
                seg_start, seg_winner = minute, winner
            prev_minute = minute

        if seg_start == prev_minute:
            segments.append(f"{seg_start}: {seg_winner}")
        else:
            segments.append(f"{seg_start}-{prev_minute}: {seg_winner}")

        bp_text = "None" if not breakpoints else ", ".join(str(v) for v in breakpoints)
        return "Scan winners | " + " ; ".join(segments) + f" | Breakpoints: {bp_text}"


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
