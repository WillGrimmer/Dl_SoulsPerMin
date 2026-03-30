"""
Souls-per-minute calculator (run length 1–60 minutes).

Game formulas live in the constants below and in boxes_total / denizen_totals / _update.
Run: python main.py
Build exe: pyinstaller --onefile --windowed --name SoulsPerMin main.py
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSlider,
    QSpinBox,
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
THREE_PERSON_SHARE_OF_TROOPER = 0.36


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

        # Minutes control dock (also listed last so it sits at the bottom of the scroll view).
        layout.addWidget(_hline())
        layout.addWidget(title)
        spin_row = QHBoxLayout()
        spin_row.addStretch(1)
        spin_row.addWidget(self.minute_spin)
        spin_row.addStretch(1)
        layout.addLayout(spin_row)
        layout.addLayout(row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)
        self.resize(960, 580)

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

        total = BASE + PER_MINUTE * minutes
        boxes = boxes_total(minutes)

        # Trooper, Wave (×4 Trooper), 2 person share (×0.54 Wave), 3 person share (×0.36 Trooper)
        self.result_value.setText(f"{total:g}")
        self.detail_label.setText(f"116 + (1.16 × {minutes})")
        wave = total * 4
        self.wave_value.setText(f"{wave:g}")
        self.wave_detail.setText("Trooper × 4")
        self.share_value.setText(f"{wave * TWO_PERSON_SHARE_OF_WAVE:g}")
        self.share_detail.setText("Wave × 0.54")
        self.share3_value.setText(f"{total * THREE_PERSON_SHARE_OF_TROOPER:g}")
        self.share3_detail.setText("Trooper × 0.36")

        self.boxes_value.setText(f"{boxes:g}")
        if minutes < 2:
            self.boxes_detail.setText("0 (before 2 min)")
        else:
            self.boxes_detail.setText(f"23 + (2 × {minutes})")
        self.boxrun_value.setText(f"{boxes * 4:g}")
        self.boxrun_detail.setText("Boxes × 4")

        # Denizen tiers, then camp rows (linear combos of t1–t3)
        t1, t2, t3 = denizen_totals(minutes)
        self.denizen_t1_value.setText(f"{t1:g}")
        self.denizen_t1_detail.setText(f"41 + (0.44 × {minutes})")
        self.denizen_t2_value.setText(f"{t2:g}")
        self.denizen_t2_detail.setText(f"68 + (0.73 × {minutes})")
        self.denizen_t3_value.setText(f"{t3:g}")
        self.denizen_t3_detail.setText(f"181 + (1.95 × {minutes})")

        self.camp_twomin_value.setText(f"{t1 * 3:g}")
        self.camp_twomin_detail.setText("3 × Tier 1")
        self.camp_medium_value.setText(f"{t2 * 3:g}")
        self.camp_medium_detail.setText("3 × Tier 2")
        self.camp_church_value.setText(f"{t1 * 4 + t2:g}")
        self.camp_church_detail.setText("4 × Tier 1 + Tier 2")
        self.camp_combo_value.setText(f"{t2 * 2 + t3:g}")
        self.camp_combo_detail.setText("2 × Tier 2 + Tier 3")
        self.camp_tripple_value.setText(f"{t3 * 3:g}")
        self.camp_tripple_detail.setText("3 × Tier 3")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
