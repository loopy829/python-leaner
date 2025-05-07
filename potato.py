import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext
import time
import threading
import csv
import os
from datetime import datetime

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("自定义番茄钟")
        self.root.geometry("350x350")
        self.root.resizable(False, False)

        self.timer_running = False
        self.remaining_time = 0
        self.session_count = 0
        self.start_time = None

        # 活动类型选择
        self.activity_label = tk.Label(root, text="选择活动类型：", font=("Arial", 12))
        self.activity_label.pack(pady=(10, 2))

        self.activity_var = tk.StringVar(value="工作")
        self.activity_menu = tk.OptionMenu(root, self.activity_var, "工作", "学习", "锻炼", "写作", "冥想")
        self.activity_menu.config(width=15)
        self.activity_menu.pack()

        # 时间输入
        self.time_label = tk.Label(root, text="设置时间（分钟）：", font=("Arial", 12))
        self.time_label.pack(pady=(10, 2))

        self.time_entry = tk.Entry(root, width=10, font=("Arial", 14), justify="center")
        self.time_entry.insert(0, "25")  # 默认25分钟
        self.time_entry.pack()

        # 倒计时显示
        self.time_display = tk.Label(root, text="00:00", font=("Arial", 36))
        self.time_display.pack(pady=10)

        # 按钮框架
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        button_width = 6  # 更小的按钮宽度
        button_height = 1  # 更小的按钮高度

        # 按钮：开始
        self.start_button = tk.Button(button_frame, text="开始", width=button_width, height=button_height, command=self.start_timer)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        # 按钮：重置
        self.reset_button = tk.Button(button_frame, text="重置", width=button_width, height=button_height, command=self.reset_timer)
        self.reset_button.grid(row=0, column=1, padx=5, pady=5)

        # 按钮：查看历史
        self.history_button = tk.Button(button_frame, text="查看历史", width=button_width, height=button_height, command=self.show_history)
        self.history_button.grid(row=1, column=0, columnspan=2, pady=5)

        # 完成次数显示
        self.count_label = tk.Label(root, text="已完成：0 次任务", font=("Arial", 12))
        self.count_label.pack(pady=10)

        # 初始化 CSV 文件
        if not os.path.exists("records.csv"):
            with open("records.csv", mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["开始时间", "结束时间", "活动类型"])

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02}:{secs:02}"

    def start_timer(self):
        if self.timer_running:
            return

        try:
            minutes = int(self.time_entry.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的分钟数！")
            return

        self.remaining_time = minutes * 60
        self.timer_running = True
        self.start_time = datetime.now()

        threading.Thread(target=self.countdown).start()

    def reset_timer(self):
        self.timer_running = False
        self.remaining_time = 0
        self.time_display.config(text="00:00")

    def countdown(self):
        while self.remaining_time > 0 and self.timer_running:
            time.sleep(1)
            self.remaining_time -= 1
            self.time_display.config(text=self.format_time(self.remaining_time))

        if self.remaining_time == 0 and self.timer_running:
            self.timer_running = False
            self.session_count += 1
            self.count_label.config(text=f"已完成：{self.session_count} 次任务")

            end_time = datetime.now()
            activity = self.activity_var.get()
            self.save_record(self.start_time, end_time, activity)

            messagebox.showinfo("时间到", f"{activity}时间结束啦！")

    def save_record(self, start_time, end_time, activity):
        with open("records.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                start_time.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                activity
            ])

    def show_history(self):
        history_window = Toplevel(self.root)
        history_window.title("历史记录")
        history_window.geometry("450x350")

        text_area = scrolledtext.ScrolledText(history_window, font=("Arial", 12))
        text_area.pack(fill="both", expand=True)

        # 检查文件是否存在
        if not os.path.exists("records.csv"):
            text_area.insert(tk.END, "暂无记录")
            return

        with open("records.csv", mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

            if len(rows) <= 1:
                text_area.insert(tk.END, "暂无记录")
                return

            # 删除重复的表头
            rows = rows[1:]

            # 设置表格的表头
            text_area.insert(tk.END, "开始时间                    | 结束时间                    | 活动类型\n")
            text_area.insert(tk.END, "-" * 50 + "\n")

            # 遍历历史记录，格式化输出
            for row in rows:
                text_area.insert(tk.END, f"{row[0]}  | {row[1]}  | {row[2]}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()