import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext
import requests
import json
import pygame
import os
import random
import threading
import time
import csv
from datetime import datetime

API_KEY = "wgweKqkeBTv2oTlQOGdpTgja"
SECRET_KEY = "PLKae9dXUZt7dWh3kM9lAwz4XUFo8iKn"

def get_access_token():
    url = f"https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    response = requests.get(url, params=params)
    return response.json().get("access_token")

def get_song_recommendation(mood):
    token = get_access_token()
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={token}"
    headers = {"Content-Type": "application/json"}
    prompt = f"我现在的心情是「{mood}」，请推荐3首适合的英文歌曲（歌名 - 歌手）"
    data = {
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json().get("result", "未获取到推荐内容")

current_mood = ""
current_song_list = []
current_song_index = 0
is_paused = False

def get_song_list_by_keyword(keyword):
    folder = "songs"
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if keyword.lower() in f.lower()]

def play_song_by_index(index):
    global current_song_list
    if index >= len(current_song_list):
        return "❌ 没有更多歌曲了"
    song = current_song_list[index]
    song_path = os.path.join("songs", song)
    pygame.mixer.init()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    return f"🎵 正在播放：{song}"

def play_local_song(keyword):
    global current_song_list, current_song_index, current_mood, is_paused
    current_mood = keyword
    current_song_list = get_song_list_by_keyword(keyword)
    current_song_index = 0
    is_paused = False
    if not current_song_list:
        return f"❌ 未找到包含「{keyword}」的本地歌曲"
    return play_song_by_index(current_song_index)

def pause_or_resume_song():
    global is_paused
    if pygame.mixer.get_init():
        if pygame.mixer.music.get_busy():
            if is_paused:
                pygame.mixer.music.unpause()
                is_paused = False
                output_text.insert(tk.END, "\n▶️ 继续播放\n")
            else:
                pygame.mixer.music.pause()
                is_paused = True
                output_text.insert(tk.END, "\n⏸ 已暂停\n")

def play_next_song():
    global current_song_index
    if not current_song_list:
        output_text.insert(tk.END, "\n⚠️ 没有歌曲播放\n")
        return
    current_song_index += 1
    if current_song_index >= len(current_song_list):
        output_text.insert(tk.END, "\n🎶 已经是最后一首啦\n")
        return
    status = play_song_by_index(current_song_index)
    output_text.insert(tk.END, "\n" + status + "\n")

def stop_music():
    pygame.mixer.music.stop()
    output_text.insert(tk.END, "\n⏹ 已停止播放\n")

def on_submit():
    mood = mood_entry.get().strip()
    if not mood:
        messagebox.showwarning("⚠️", "请输入你的心情！")
        return
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "🤖 正在获取推荐...\n")
    root.update()
    try:
        result = get_song_recommendation(mood)
        output_text.insert(tk.END, f"🎧 推荐结果：\n{result}\n\n")
        status = play_local_song(mood)
        output_text.insert(tk.END, status)
    except Exception as e:
        output_text.insert(tk.END, f"❌ 出错：{str(e)}")

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.timer_running = False
        self.remaining_time = 0
        self.session_count = 0
        self.start_time = None
        tk.Label(root, text="选择活动类型：", font=("Arial", 12)).pack()
        self.activity_var = tk.StringVar(value="工作")
        tk.OptionMenu(root, self.activity_var, "工作", "学习", "锻炼", "写作", "冥想").pack()
        tk.Label(root, text="设置时间（分钟）：", font=("Arial", 12)).pack()
        self.time_entry = tk.Entry(root, width=10, font=("Arial", 14), justify="center")
        self.time_entry.insert(0, "25")
        self.time_entry.pack()
        self.time_display = tk.Label(root, text="00:00", font=("Arial", 36))
        self.time_display.pack(pady=10)
        f = tk.Frame(root)
        f.pack()
        tk.Button(f, text="开始", width=6, command=self.start_timer).grid(row=0, column=0, padx=5)
        tk.Button(f, text="重置", width=6, command=self.reset_timer).grid(row=0, column=1, padx=5)
        tk.Button(f, text="查看历史", width=13, command=self.show_history).grid(row=1, column=0, columnspan=2, pady=5)
        self.count_label = tk.Label(root, text="已完成：0 次任务", font=("Arial", 12))
        self.count_label.pack(pady=10)
        if not os.path.exists("records.csv"):
            with open("records.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["开始时间", "结束时间", "活动类型"])

    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"

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
            self.save_record(self.start_time, datetime.now(), self.activity_var.get())
            messagebox.showinfo("时间到", f"{self.activity_var.get()}时间结束啦！")

    def save_record(self, start, end, activity):
        with open("records.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S"), activity])

    def show_history(self):
        win = Toplevel(self.root)
        win.title("历史记录")
        win.geometry("450x350")
        area = scrolledtext.ScrolledText(win, font=("Arial", 12))
        area.pack(fill="both", expand=True)
        if not os.path.exists("records.csv"):
            area.insert(tk.END, "暂无记录")
            return
        with open("records.csv", "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]
            area.insert(tk.END, "开始时间                    | 结束时间                    | 活动类型\n")
            area.insert(tk.END, "-" * 50 + "\n")
            for row in rows:
                area.insert(tk.END, f"{row[0]}  | {row[1]}  | {row[2]}\n")

root = tk.Tk()
root.title("效率工具箱：音乐推荐 + 番茄钟")
root.geometry("580x720")

frame1 = tk.LabelFrame(root, text="🎵 AI 心情音乐推荐", padx=10, pady=10)
frame1.pack(fill="x", padx=10, pady=5)

mood_entry = tk.Entry(frame1, font=("Arial", 14), width=30)
mood_entry.pack()
tk.Button(frame1, text="获取推荐并播放", command=on_submit).pack(pady=5)

btns = tk.Frame(frame1)
btns.pack()
tk.Button(btns, text="暂停/继续", command=pause_or_resume_song).pack(side="left", padx=5)
tk.Button(btns, text="下一首", command=play_next_song).pack(side="left", padx=5)
tk.Button(btns, text="停止播放", command=stop_music).pack(side="left", padx=5)

output_text = tk.Text(frame1, height=8)
output_text.pack(fill="x")

frame2 = tk.LabelFrame(root, text="🍅 番茄工作法", padx=10, pady=10)
frame2.pack(fill="both", expand=True, padx=10, pady=5)
PomodoroTimer(frame2)

root.mainloop()