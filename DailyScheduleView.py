import sqlite3  # Use SQlite for database operations

from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout,
                            QSizePolicy, QPushButton, QDialog, QFormLayout, QLineEdit, 
                            QColorDialog, QDialogButtonBox, QCalendarWidget,
                            QGraphicsTextItem, QGraphicsRectItem,QMenu,QInputDialog)

from PyQt6.QtCore import Qt, QDate, QPoint, QPropertyAnimation, QEasingCurve

from PyQt6.QtGui import (QColor, QTextCharFormat, QFont, QBrush, QPen, QPainter, 
                         )


import random

# 柔和色板，卡片背景随机选色
PALETTE = [
    QColor("#FFD2D2"),
    QColor("#D2EAFD"),
    QColor("#D2FDD9"),
    QColor("#FDE2D2"),
    QColor("#F2D2FD"),
]

class EventItem(QGraphicsRectItem):
    def __init__(self, event_data, pixels_per_minute):
        super().__init__()
        self.event_data = event_data
        self.pixels_per_minute = pixels_per_minute

        # 计算时间位置
        start_min = event_data["start_time"].hour() * 60 + event_data["start_time"].minute()
        end_min = event_data["end_time"].hour() * 60 + event_data["end_time"].minute()
        duration = end_min - start_min
        
        # 设置图形属性
        self.setRect(0, 0, 200, duration * self.pixels_per_minute)
        self.setPos(50, start_min * self.pixels_per_minute)  # 左边留出50px空间
        self.setBrush(QBrush(event_data["color"]))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        
        # 添加文字标签
        text = QGraphicsTextItem(
            f"{event_data['title']}\n"
            f"{event_data['start_time'].toString('HH:mm')} - {event_data['end_time'].toString('HH:mm')}",
            parent=self
        )
        text.setDefaultTextColor(Qt.GlobalColor.white)
        text.setPos(5, 5)  # 文字内边距

# 一个简单的事件卡片类
class EventCard(QFrame):
    def __init__(
        self,
        title: str,
        place: str,
        start_hour: int, start_min: int,
        end_hour:   int, end_min:   int,
        color:      QColor,
        scheduler_view,  # 新增：指向 DailyScheduleView 实例
        date,            # 新增：所属 QDate
        idx: int,        # 新增：该事件在列表中的索引
        parent=None
    ):
        super().__init__(parent)
        self.scheduler_view = scheduler_view
        self.date            = date
        self.idx             = idx

        # 如果没有传 color，则随机指定一个
        if color is None:
            from PyQt6.QtGui import QColor
            color = QColor("#4dabf7")
        """    
        css_color = color.name()
        self.setStyleSheet(f"background-color: {css_color}; border-radius: 4px;")
        """

        r, g, b = color.red(), color.green(), color.blue()
        self.setStyleSheet(
            f"background-color: rgba({r}, {g}, {b}, 0.5);"
            "border-radius: 4px;"
        )

        # 根据时长计算高度
        minutes = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
        px_per_min = scheduler_view.canvas.hour_height / 60
        self.setFixedHeight(int(minutes * px_per_min))

        # 文本：标题、地点、时间
        text = (
            f"{title}\n"
            f"📍 {place}\n"
            f"⏰ {start_hour:02d}:{start_min:02d} – {end_hour:02d}:{end_min:02d}"
        )
        lbl = QLabel(text, self)
        lbl.setStyleSheet("color: white; font-weight: bold;")
        lbl.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.addWidget(lbl)

        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)


    def _show_context_menu(self, pos: QPoint):
            menu = QMenu(self)
            act_name = menu.addAction("Edit Title✏️")
            act_place = menu.addAction("Edit Place📍")
            act_time  = menu.addAction("Edit Time & Color🎨")
            act_nav   = menu.addAction("Navigate to Place🗺️")
            act_del   = menu.addAction("Delete 🗑️")
            
            action = menu.exec(self.mapToGlobal(pos))
            if action == act_nav:
                self.scheduler_view.navigate_event(self.date, self.idx)
            elif action == act_del:
                self.scheduler_view.delete_event(self.date, self.idx)
            elif action == act_place:
                self.scheduler_view.edit_event_place(self.date, self.idx)
            elif action == act_time:
                self.scheduler_view.edit_event_time_color(self.date, self.idx)
            elif action == act_name:
                self.scheduler_view.edit_event_name(self.date, self.idx)


# 网格画布类
class GridCanvas(QWidget):
    def __init__(self, hour_height=60, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hour_height = hour_height

    def paintEvent(self, ev):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.gray)
        painter.setPen(pen)
        w = self.width()
        # 画 0 到 24 条水平线
        for h in range(25):
            y = h * self.hour_height
            painter.drawLine(0, y, w, y)
        super().paintEvent(ev)


# 添加事件对话框
class AddEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Event")
        self.setFixedWidth(300)

        layout = QFormLayout(self)
        self.title_input = QLineEdit(); layout.addRow("Title:", self.title_input)
        self.place_input = QLineEdit(); layout.addRow("Place:", self.place_input)
        self.start_time_input = QLineEdit(); layout.addRow("Start Time (HH:MM):", self.start_time_input)
        self.end_time_input   = QLineEdit(); layout.addRow("End Time   (HH:MM):", self.end_time_input)
        self.color_btn        = QPushButton("Pick Color"); layout.addRow("Color:", self.color_btn)
        self.color = QColor("#0078d4")
        self.color_btn.clicked.connect(self.pick_color)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                   QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def pick_color(self):
        c = QColorDialog.getColor()
        if c.isValid(): self.color = c

    def get_data(self):
        title = self.title_input.text().strip()
        place = self.place_input.text().strip()
        try:
            sh, sm = map(int, self.start_time_input.text().split(":"))
            eh, em = map(int, self.end_time_input.text().split(":"))
        except:
            return None
        return title, place, sh, sm, eh, em, self.color


# DailyScheduleView 类
# 这是一个日历视图，显示每天的事件安排
class DailyScheduleView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Database
        self.db_conn = sqlite3.connect('resources/misc/events.db')
        self.db_cursor = self.db_conn.cursor()

        # Table指令
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                date TEXT,
                title TEXT,
                place TEXT,
                start TEXT,
                end TEXT,
                color TEXT
            )
        ''')

        self.db_conn.commit()

        # load events
        self.events_by_date = {}
        self.load_events()

        # UI
        self.setWindowTitle("Daily Schedule View")
        self.current_date = QDate.currentDate()
        root_layout = QVBoxLayout(self)

        # Header: calendar + add
        header = QHBoxLayout()
        self.date_label = QLabel(self.current_date.toString("dddd MMMM d"))
        self.date_label.setStyleSheet("font-weight:bold; font-size:16px; color:white;")
        header.addWidget(self.date_label)
        toggle = QPushButton("+ Add Event")
        toggle.clicked.connect(self.open_add_dialog)
        header.addWidget(toggle)
        root_layout.addLayout(header)
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumHeight(200)
        self.calendar.clicked.connect(self.on_date_selected)

        self.apply_calendar_formatting()

        root_layout.addWidget(self.calendar)

        # Scroll area with axis + grid canvas
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
        root_layout.addWidget(scroll_area)
        container = QWidget(); scroll_area.setWidget(container)
        hl = QHBoxLayout(container); hl.setContentsMargins(0,0,0,0)

        # axis
        hour_h = 60
        axis = QWidget(); vl = QVBoxLayout(axis); vl.setContentsMargins(0,0,0,0)
        for h in range(24):
            lbl = QLabel(f"{h:02d}:00")
            lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            lbl.setStyleSheet("padding-right:4px; color:gray;")
            vl.addWidget(lbl)
        hl.addWidget(axis, 0)

        # canvas
        self.canvas = GridCanvas(hour_height=hour_h, parent=container)
        self.canvas.setMinimumHeight(24 * hour_h)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        hl.addWidget(self.canvas, 1)

        # resize patch
        def on_resize(ev):
            QWidget.resizeEvent(self.canvas, ev)
            for card in self.canvas.findChildren(EventCard):
                card.setFixedWidth(self.canvas.width())
        self.canvas.resizeEvent = on_resize

        # initial render
        self.render_events_for_date(self.current_date)

    def apply_calendar_formatting(self):
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        today = QDate.currentDate()
        fmt_today = QTextCharFormat()
        fmt_today.setForeground(Qt.GlobalColor.red)
        fmt_today.setFontWeight(QFont.Weight.Bold)
        self.calendar.setDateTextFormat(today, fmt_today)

        weekend_fmt = QTextCharFormat()
        weekend_fmt.setForeground(Qt.GlobalColor.gray)

        for year in range(today.year() - 1, today.year() + 2):
            for month in range(1, 13):
                for day in range(1, 32):
                    date = QDate(year, month, day)
                    if date.isValid() and date.dayOfWeek() in (6, 7):
                        self.calendar.setDateTextFormat(date, weekend_fmt)

    def update_views(self):
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("#0078d4")))
        self.calendar_view.setDateTextFormat(self.current_date, fmt)
        
        self.date_label.setText(self.current_date.toString("dddd, MMMM d"))
        self.time_axis.scene.clear()
        self.time_axis.draw_time_marks()
        
        date_str = self.current_date.toString(Qt.DateFormat.ISODate)
        for event in self.events.get(date_str, []):
            event_item = EventItem(event, self.pixels_per_minute)
            self.time_axis.scene.addItem(event_item)                    


    """
    添加新事件
    """
    def add_event(self, title, place, sh, sm, eh, em, color: QColor):
        # 1) 写入 SQLite，记得插入 place 和 color
        dstr = self.current_date.toString(Qt.DateFormat.ISODate)
        self.db_cursor.execute(
            'INSERT INTO events (date, title, place, start, end, color) VALUES (?, ?, ?, ?, ?, ?)',
            (dstr, title, place,
             f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}",
             color.name())
        )
        self.db_conn.commit()

        # 2) 更新内存缓存
        self.events_by_date.setdefault(self.current_date, []).append(
            (title, place, sh, sm, eh, em, color)
        )

        # 3) 刷新 UI
        self.render_events_for_date(self.current_date)

    def open_add_dialog(self):
        dlg = AddEventDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            if data:
                title, place, sh, sm, eh, em, color = data
                # 先写入 DB，再刷新
                self.add_event(title, place, sh, sm, eh, em, color)


    """
    获取当天所有空闲时段列表
    """
    def get_free_slots(self, date: QDate) -> list[tuple[int,int,int,int]]:
        """
        返回当天所有空闲时段，格式 [(sh, sm, eh, em), …]
        依照分钟数排序。
        """
        # 1) 事件列表：每项 (title, place, sh, sm, eh, em, color)
        evs = sorted(
            self.events_by_date.get(date, []),
            key=lambda e: e[2] * 60 + e[3]  # 用 sh, sm 排序
        )

        slots = []
        prev_end = 0  # 从 00:00 开始

        # 2) 依次找空隙
        for title, place, sh, sm, eh, em, color in evs:
            start_min = sh * 60 + sm
            if start_min > prev_end:
                # prev_end 到 start_min 之间是空闲
                slots.append((prev_end // 60, prev_end % 60, sh, sm))
            prev_end = max(prev_end, eh * 60 + em)

        # 3) 最后从最后一个事件到 24:00 的空隙
        if prev_end < 24 * 60:
            slots.append((prev_end // 60, prev_end % 60, 24, 0))

        return slots


    def on_date_selected(self, date):
        self.date_label.setText(date.toString("dddd MMMM d"))
        self.current_date = date
        self.render_events_for_date(date)
        self.apply_calendar_formatting()
        
    def toggle_calendar_view(self):
        self.animation = QPropertyAnimation(self.calendar, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        if self.calendar_expanded:
            self.animation.setStartValue(300)
            self.animation.setEndValue(0)
        else:
            self.animation.setStartValue(0)
            self.animation.setEndValue(300)
        self.animation.start()
        self.calendar_expanded = not self.calendar_expanded


    """
    渲染事件
    """
    def render_events_for_date(self, date: QDate):
        # 1) 清掉画布上旧的卡片
        for child in self.canvas.findChildren(EventCard):
            child.deleteLater()

        # 2) 每分钟对应的像素
        px_per_min = self.canvas.hour_height / 60

        # 3) 取当天的所有事件
        events = self.events_by_date.get(date, [])

        # 4) 按顺序渲染
        for idx, (title, place, sh, sm, eh, em, color) in enumerate(events):
            start_min = sh * 60 + sm
            duration  = (eh * 60 + em) - start_min
            y = start_min * px_per_min
            h = duration   * px_per_min

            # 5) 实例化 EventCard —— 传入 scheduler_view、date、idx
            card = EventCard(
                title, 
                place,
                sh, sm, 
                eh, em,
                color,
                scheduler_view=self,
                date=date,
                idx=idx,
                parent=self.canvas
            )

            # 6) 放到正确的位置和大小
            card.setGeometry(0, int(y), self.canvas.width(), int(h))
            card.show()


    """
    读取事件
    """
    def load_events(self):
        self.db_cursor.execute(
            'SELECT date, title, place, start, end, color FROM events'
        )
        for date_str, title, place, start_s, end_s, color_s in self.db_cursor.fetchall():
            qd = QDate.fromString(date_str, Qt.DateFormat.ISODate)
            if not qd.isValid():
                continue
            sh, sm = map(int, start_s.split(':'))
            eh, em = map(int, end_s.split(':'))
            col = QColor(color_s)
            self.events_by_date.setdefault(qd, []).append(
                (title, place, sh, sm, eh, em, col)
            )

    def delete_event(self, date: QDate, idx: int):
        """
        删除 events_by_date[date] 中序号为 idx 的事件，
        并同步到 SQLite 数据库，然后刷新界面。
        """
        # 1) 从内存缓存中移除
        events = self.events_by_date.get(date, [])
        if idx < 0 or idx >= len(events):
            return
        title, place, sh, sm, eh, em, color = events.pop(idx)

        # 2) 从数据库中删除（按日期+标题+地点+开始+结束 精确匹配）
        dstr = date.toString(Qt.DateFormat.ISODate)
        start_s = f"{sh:02d}:{sm:02d}"
        end_s   = f"{eh:02d}:{em:02d}"
        self.db_cursor.execute(
            "DELETE FROM events WHERE date = ? AND title = ? AND place = ? AND start = ? AND end = ?",
            (dstr, title, place, start_s, end_s)
        )
        self.db_conn.commit()

        # 3) 刷新当前视图
        self.render_events_for_date(date)


    """
    修改地点
    """
    def edit_event_place(self, date, idx):
        # 读取旧值
        ev = list(self.events_by_date[date][idx])
        old_place = ev[1]
        # 弹出对话框让用户输入新地点
        new_place, ok = QInputDialog.getText(self, "Edit Place", "Place:", text=old_place)
        if not ok or not new_place.strip():
            return
        ev[1] = new_place.strip()
        self.events_by_date[date][idx] = tuple(ev)
        # 更新数据库
        dstr = date.toString(Qt.DateFormat.ISODate)
        self.db_cursor.execute(
            'UPDATE events SET place = ? WHERE date = ? AND title = ? AND start = ? AND end = ?',
            (
                new_place.strip(), dstr,
                ev[0],
                f"{ev[2]:02d}:{ev[3]:02d}",
                f"{ev[4]:02d}:{ev[5]:02d}"
            )
        )
        self.db_conn.commit()
        self.render_events_for_date(date)    


    """
    修改时间和颜色
    """
    def edit_event_time_color(self, date: QDate, idx: int):
        # 1) 取出旧值
        ev = list(self.events_by_date[date][idx])
        # ev 格式现在是 [ title, place, start_h, start_m, end_h, end_m, color ]

        # 2) 让对话框支持全天任意选，隐藏下拉
        from RecommendationView import TimeSlotDialog
        # 用 00:00–23:59 作为全日可选范围
        dlg = TimeSlotDialog([(0, 0, 23, 59)], self)
        dlg.slot_combo.hide()

        # 3) 预置对话框中的时间和颜色为当前事件值
        from PyQt6.QtCore import QTime
        orig_sh, orig_sm, orig_eh, orig_em = ev[2], ev[3], ev[4], ev[5]
        dlg.start_edit.setTime(QTime(orig_sh, orig_sm))
        dlg.end_edit  .setTime(QTime(orig_eh, orig_em))

        # 如果原来存的是字符串，再转成 QColor
        from PyQt6.QtGui import QColor
        old_color = ev[6]
        c = QColor(old_color) if isinstance(old_color, str) else old_color
        dlg.color = c
        dlg.color_btn.setStyleSheet(f"background-color: {c.name()};")

        # 4) 弹窗并拿回新值
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_sh, new_sm, new_eh, new_em, new_color = dlg.get_times()

        # 5) 更新内存和数据库
        ev[2], ev[3], ev[4], ev[5], ev[6] = new_sh, new_sm, new_eh, new_em, new_color
        self.events_by_date[date][idx] = tuple(ev)

        dstr = date.toString(Qt.DateFormat.ISODate)
        self.db_cursor.execute(
            '''
            UPDATE events
               SET start = ?, end = ?, color = ?
             WHERE date  = ?
               AND title = ?
            ''',
            (
                f"{new_sh:02d}:{new_sm:02d}",
                f"{new_eh:02d}:{new_em:02d}",
                new_color.name(),
                dstr,
                ev[0]
            )
        )
        self.db_conn.commit()

        # 6) 重新渲染
        self.render_events_for_date(date)


    """
    右键导航
    """
    def navigate_event(self, date: QDate, idx: int):
        """
        右键 “Navigate to Place…” 调用这里，  
        切到 MapView 页面并在内嵌的谷歌地图里显示导航。
        """
        # 取出目标地点
        _, place, sh, sm, eh, em, _ = self.events_by_date[date][idx]

        # 准备 URL 参数（空格转 +）
        #origin = "Current+Location"
        origin = "My+Location"
        destination = place.replace(" ", "+")

        # 找到主窗口实例，并切到 mapInterface
        main_win = self.window()  
        main_win.switchTo(main_win.mapInterface)

        # 让 mapInterface 加载导航
        main_win.mapInterface.navigate(origin, destination)
    
    """
    右键修改日程名称
    """
    def edit_event_name(self, date: QDate, idx: int):
        # 读取旧值
        ev = list(self.events_by_date[date][idx])
        old_title = ev[0]
        # 弹出对话框让用户输入新名称
        new_title, ok = QInputDialog.getText(self, "Edit Title", "Title:", text=old_title)
        if not ok or not new_title.strip():
            return
        ev[0] = new_title.strip()
        self.events_by_date[date][idx] = tuple(ev)
        # 更新数据库
        dstr = date.toString(Qt.DateFormat.ISODate)
        self.db_cursor.execute(
            'UPDATE events SET title = ? WHERE date = ? AND title = ? AND start = ? AND end = ?',
            (
                new_title.strip(), dstr,
                old_title.strip(),
                f"{ev[2]:02d}:{ev[3]:02d}",
                f"{ev[4]:02d}:{ev[5]:02d}"
            )
        )
        self.db_conn.commit()  # 提交更改
        self.render_events_for_date(date)  # 刷新当前视图


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = DailyScheduleView()
    window.resize(700, 1000)
    window.show()
    sys.exit(app.exec())