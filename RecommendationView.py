# RecommendationView.py

import random

import json
import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QComboBox, QTimeEdit, QDialogButtonBox, QColorDialog
)

from PyQt6.QtCore import QTime

from openai import OpenAI

# 读取 Deepseek 配置
with open("resources/misc/config.json", "r") as f:
    _config = json.load(f)
DEEPSEEK_KEY = _config.get("deepseek_api_key", "").strip()

class TimeSlotDialog(QDialog):
    def __init__(self, slots: list[tuple[int,int,int,int]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Time Slot")
        self.resize(320, 200)

        main_layout = QVBoxLayout(self)
        form = QFormLayout()
        main_layout.addLayout(form)

        # 1) 下拉选择可用 Gap
        self.slot_combo = QComboBox(self)
        for sh, sm, eh, em in slots:
            text = f"{sh:02d}:{sm:02d} – {eh:02d}:{em:02d}"
            self.slot_combo.addItem(text, (sh, sm, eh, em))
        form.addRow("Free slots:", self.slot_combo)

        # 2) 时间编辑器：可在 Gap 内自由调整
        times_widget = QWidget(self)
        times_layout = QVBoxLayout(times_widget)
        times_layout.setContentsMargins(0, 0, 0, 0)
        self.start_edit = QTimeEdit(times_widget)
        self.start_edit.setDisplayFormat("HH:mm")
        self.end_edit = QTimeEdit(times_widget)
        self.end_edit.setDisplayFormat("HH:mm")
        times_layout.addWidget(self.start_edit)
        times_layout.addWidget(self.end_edit)
        form.addRow("Start / End:", times_widget)

        # 3) 颜色选择按钮
        self.color_btn = QPushButton("Pick Color", self)
        self.color = QColor("#4dabf7")  # 默认色
        form.addRow("Color:", self.color_btn)
        self.color_btn.clicked.connect(self._pick_color)

        # 每次切换 Gap 时，刷新时间上下限和默认值
        self.slot_combo.currentIndexChanged.connect(self._on_slot_changed)
        self._on_slot_changed(0)

        # 4) 确定 / 取消 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    """
    修改下拉框时，更新时间编辑器的上下限和默认值
    """
    def _on_slot_changed(self, idx: int):
        sh, sm, eh, em = self.slot_combo.currentData()
        min_t = QTime(sh, sm)
        #max_t = QTime(eh, em)

        # clamp any 24:00 → 23:59 for the maximum
        if eh >= 24:
            max_t = QTime(23, 59)
        else:
            max_t = QTime(eh, em)

        self.start_edit.setMinimumTime(min_t)
        self.start_edit.setMaximumTime(max_t)
        self.start_edit.setTime(min_t)

        self.end_edit.setMinimumTime(min_t)
        self.end_edit.setMaximumTime(max_t)
        self.end_edit.setTime(max_t)

    def _pick_color(self):
        c = QColorDialog.getColor(self.color, self, "Choose Event Color")
        if c.isValid():
            self.color = c
            self.color_btn.setStyleSheet(f"background-color: {c.name()};")

    def get_times(self) -> tuple[int,int,int,int,QColor]:
        """
        返回 (start_h, start_m, end_h, end_m, color)
        """
        st = self.start_edit.time()
        et = self.end_edit.time()
        return (st.hour(), st.minute(), et.hour(), et.minute(), self.color)


class RecommendationView(QWidget):
    def __init__(self, scheduler, parent=None):
        super().__init__(parent)
        self.scheduler = scheduler

        self.recs = []
        
        # 总布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 标题
        title = QLabel("📋 Recommendations", self)
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        layout.addWidget(title)

        # 1) Location 输入
        self.location_input = QLineEdit(self)
        self.location_input.setPlaceholderText("Enter your location (e.g., Singapore)")
        layout.addWidget(self.location_input)

        # 2) Interests 输入
        self.tag_input = QLineEdit(self)
        self.tag_input.setPlaceholderText(
            "Enter interests (comma-separated, e.g., exercise, culture)"
        )
        layout.addWidget(self.tag_input)

        # 3) Generate 按钮
        self.gen_button = QPushButton("Generate", self)
        layout.addWidget(self.gen_button)

        # 4) 结果表格：3 列，最后一列放 Add 按钮
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Place", "Reason", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, stretch=1)

        # Deepseek 客户端
        if DEEPSEEK_KEY:
            self.ds_client = OpenAI(
                api_key=DEEPSEEK_KEY,
                base_url="https://api.deepseek.com"
            )
        else:
            self.ds_client = None

        # 事件绑定
        self.gen_button.clicked.connect(self.on_generate)


    """
    生成推荐的函数
    """
    def on_generate(self):
        from PyQt6.QtWidgets import QTableWidgetItem, QProgressDialog
        import re, json

        # 1) 清空表格和上一轮结果
        self.table.setRowCount(0)
        self.recs = []

        # 2) 校验输入
        location = self.location_input.text().strip()
        if not location:
            return self._show_error("⚠️ Please enter your location.")
        tags = [t.strip() for t in self.tag_input.text().split(",") if t.strip()]
        if not tags:
            return self._show_error("⚠️ Please enter at least one interest tag.")
        if not self.ds_client:
            return self._show_error("⚠️ Deepseek API key missing in config.json.")

        # 3) 构造 Prompt
        prompt = (
            f"I am in {location}. My interests are: {', '.join(tags)}. "
            "Please recommend 5 places or activities in this location. "
            "Respond only as a JSON array of objects, "
            "each with 'place' and 'reason' fields—no extra text or Markdown fences."
        )
        messages = [
            {"role": "system", "content": "You are a friendly local tour guide."},
            {"role": "user",   "content": prompt}
        ]

        # 4) 加载提示
        dlg = QProgressDialog("Loading recommendations...", None, 0, 0, self)
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setCancelButton(None)
        dlg.show()

        try:
            # 5) 调用 Deepseek
            resp = self.ds_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )
            raw = resp.choices[0].message.content.strip()

            # 6) 清理 Markdown 围栏
            text = re.sub(r"^```(?:json)?\s*", "", raw)
            text = re.sub(r"\s*```$", "", text)
            text = text.replace("`", "").strip()

            # 7) 解析 JSON，并保存到 self.recs
            try:
                items = json.loads(text)
            except json.JSONDecodeError:
                return self._show_error("❌ Invalid JSON response.", raw)
            self.recs = items

            # 8) 填充表格，每行最后一列放 “Add” 按钮
            for row, rec in enumerate(self.recs):
                place  = rec.get("place", "")
                reason = rec.get("reason", "")

                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(place))
                self.table.setItem(row, 1, QTableWidgetItem(reason))

                btn = QPushButton("Add", self)
                # 用默认参数锁定当前 row
                btn.clicked.connect(lambda _, r=row: self._add_recommendation(r))
                self.table.setCellWidget(row, 2, btn)

            # 9) 自适应行高
            self.table.resizeRowsToContents()

        except Exception as e:
            self._show_error(f"❌ Recommendation failed: {e}")
        finally:
            dlg.close()


    """
    一键添加日程的框的函数
    """
    def _add_recommendation(self, row: int):
        rec = self.recs[row]
        place = rec["place"]

        # 1) 取得当天所有空闲时段
        slots = self.scheduler.get_free_slots(self.scheduler.current_date)

        # 2) 一定要走弹窗，让用户选时间 & 颜色
        dlg = TimeSlotDialog(slots, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        sh, sm, eh, em, color = dlg.get_times()

        # 3) 真正把这五个值传给日程接口
        #    add_event(self, title, place, sh, sm, eh, em, color)
        title = rec.get("reason", place)
        self.scheduler.add_event(title, place, sh, sm, eh, em, color)


    def _show_error(self, msg: str, raw: str = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem(msg)
        item.setForeground(Qt.GlobalColor.red)
        self.table.setItem(row, 0, item)
        self.table.setSpan(row, 0, 1, 3)
        if raw:
            row2 = self.table.rowCount()
            self.table.insertRow(row2)
            raw_item = QTableWidgetItem(raw)
            raw_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row2, 0, raw_item)
            self.table.setSpan(row2, 0, 1, 3)
        self.table.resizeRowsToContents()
