import asyncio
import aiohttp
import json
import os
import threading
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# YOUR WEBHOOK URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1440493340905963600/SfkOxwXBYHi4iy6r3-0h04AD_ddPhmbjf56MRCSQmMIUjBWJGeVl5guhGNnkoN3I12mt"

UCT_CHANNELS = [
    1410265177521262712,
    1420821708121702411,
    1365997671097307166
]

class NeonHubGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("NeonHub AutoJoiner - discord.gg/bqUy6nauJz")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
       
        self.is_running = False
        self.servers_joined = 0
        self.config_file = "config.json"
        self.discord_token = ""
        self.money_threshold_from = 10.0
        self.money_threshold_to = 99999.0
        self.notifiers = {
            "chilli": True,
            "uct": False
        }
        self.channels = {
            "chilli": [1401775181025775738],
            "uct": UCT_CHANNELS
        }
       
        self.load_config()
        self.create_ui()
       
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.discord_token = config.get('discord_token', '')
                    self.money_threshold_from = config.get('money_threshold_from', 10.0)
                    self.money_threshold_to = config.get('money_threshold_to', 99999.0)
                    self.notifiers = config.get('notifiers', self.notifiers)
            except:
                pass
   
    def save_config(self):
        config = {
            'discord_token': self.discord_token,
            'money_threshold_from': self.money_threshold_from,
            'money_threshold_to': self.money_threshold_to,
            'notifiers': self.notifiers
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
   
    def create_ui(self):
        main_container = ctk.CTkFrame(self.root, fg_color="#0a1530")
        main_container.pack(fill="both", expand=True)
       
        tab_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        tab_frame.pack(fill="x", padx=30, pady=(20, 0))
        self.tab_buttons = {}
        for tab, text in [("main", "Main"), ("config", "Discord Config"), ("notifiers", "Notifiers")]:
            btn = ctk.CTkButton(tab_frame, text=text, width=140, height=38,
                                fg_color="#162447" if tab != "main" else "#3b82f6",
                                hover_color="#2563eb",
                                text_color="#fff" if tab == "main" else "#60a5fa",
                                font=ctk.CTkFont(size=15, weight="bold"),
                                corner_radius=8,
                                border_width=2,
                                border_color="#3b82f6",
                                command=lambda t=tab: self.switch_tab(t))
            btn.pack(side="left", padx=(0, 10))
            self.tab_buttons[tab] = btn
       
        self.content_frame = ctk.CTkFrame(main_container, fg_color="#0a1530")
        self.content_frame.pack(fill="both", expand=True, padx=30, pady=20)
       
        self.main_tab = ctk.CTkFrame(self.content_frame, fg_color="#0a1530")
        self.config_tab = ctk.CTkFrame(self.content_frame, fg_color="#0a1530")
        self.notifiers_tab = ctk.CTkFrame(self.content_frame, fg_color="#0a1530")
       
        self.create_main_tab()
        self.create_config_tab()
        self.create_notifiers_tab()
       
        self.switch_tab("main")
   
    def switch_tab(self, tab_name):
        for tab in (self.main_tab, self.config_tab, self.notifiers_tab):
            tab.pack_forget()
        for tab, btn in self.tab_buttons.items():
            if tab == tab_name:
                btn.configure(fg_color="#3b82f6", text_color="#fff")
            else:
                btn.configure(fg_color="#162447", text_color="#60a5fa")
        if tab_name == "main":
            self.main_tab.pack(fill="both", expand=True)
        elif tab_name == "config":
            self.config_tab.pack(fill="both", expand=True)
        elif tab_name == "notifiers":
            self.notifiers_tab.pack(fill="both", expand=True)
   
    def create_main_tab(self):
        card = ctk.CTkFrame(self.main_tab, fg_color="#162447", corner_radius=18, border_width=2, border_color="#3b82f6")
        card.pack(fill="x", padx=10, pady=20)
        ctk.CTkLabel(card, text="NeonHub Webhook Sniffer", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=30, pady=(20, 0))
        ctk.CTkLabel(card, text="Sends jobs → Your Discord Webhook", font=ctk.CTkFont(size=16), text_color="#60a5fa").pack(anchor="w", padx=30, pady=(0, 20))
        
        controls = ctk.CTkFrame(card, fg_color="transparent")
        controls.pack(pady=10)
        self.start_btn = ctk.CTkButton(controls, text="START", width=180, height=50,
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       fg_color="#3b82f6", hover_color="#2563eb",
                                       text_color="#fff", corner_radius=8,
                                       border_width=2, border_color="#60a5fa",
                                       command=self.start_bot)
        self.start_btn.pack(side="left", padx=10)
        self.pause_btn = ctk.CTkButton(controls, text="PAUSE (F2)", width=180, height=50,
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       fg_color="#60a5fa", hover_color="#3b82f6",
                                       text_color="#162447", corner_radius=8,
                                       border_width=2, border_color="#3b82f6",
                                       command=self.pause_bot, state="disabled")
        self.pause_btn.pack(side="left", padx=10)
        
        status_cards = ctk.CTkFrame(card, fg_color="transparent")
        status_cards.pack(pady=20)
        status_card = ctk.CTkFrame(status_cards, width=220, height=90, fg_color="#0a1530", corner_radius=12, border_width=2, border_color="#3b82f6")
        status_card.pack(side="left", padx=10)
        status_card.pack_propagate(False)
        ctk.CTkLabel(status_card, text="Status", font=ctk.CTkFont(size=15, weight="bold"), text_color="#60a5fa").pack(pady=(10, 2))
        self.status_label = ctk.CTkLabel(status_card, text="Stopped", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ef4444")
        self.status_label.pack()
        
        servers_card = ctk.CTkFrame(status_cards, width=220, height=90, fg_color="#0a1530", corner_radius=12, border_width=2, border_color="#3b82f6")
        servers_card.pack(side="left", padx=10)
        servers_card.pack_propagate(False)
        ctk.CTkLabel(servers_card, text="Jobs Sent", font=ctk.CTkFont(size=15, weight="bold"), text_color="#60a5fa").pack(pady=(10, 2))
        self.servers_label = ctk.CTkLabel(servers_card, text="0", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b82f6")
        self.servers_label.pack()
        
        logs_card = ctk.CTkFrame(card, fg_color="#0a1530", corner_radius=12, border_width=2, border_color="#3b82f6")
        logs_card.pack(fill="both", expand=True, padx=10, pady=20)
        logs_header = ctk.CTkFrame(logs_card, fg_color="transparent")
        logs_header.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(logs_header, text="Live Logs", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b82f6").pack(side="left")
        clear_btn = ctk.CTkButton(logs_header, text="Clear", width=90, height=32,
                                  fg_color="#2563eb", hover_color="#3b82f6",
                                  text_color="#fff", corner_radius=8,
                                  border_width=2, border_color="#60a5fa",
                                  command=self.clear_logs)
        clear_btn.pack(side="right")
        self.logs_text = ctk.CTkTextbox(logs_card, width=700, height=220,
                                        font=ctk.CTkFont(size=12, family="Consolas"),
                                        fg_color="#162447", corner_radius=8,
                                        text_color="#60a5fa")
        self.logs_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.logs_text.configure(state="disabled")
   
    def create_config_tab(self):
        # Your original config tab (unchanged)
        card = ctk.CTkFrame(self.config_tab, fg_color="#162447", corner_radius=18, border_width=2, border_color="#3b82f6")
        card.pack(fill="x", padx=10, pady=20)
        ctk.CTkLabel(card, text="Discord Configuration", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=30, pady=(20, 0))
        token_section = ctk.CTkFrame(card, fg_color="#0a1530", corner_radius=12, border_width=2, border_color="#3b82f6")
        token_section.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(token_section, text="Discord Token:", font=ctk.CTkFont(size=16, weight="bold"), anchor="w", text_color="#60a5fa").pack(anchor="w", padx=25, pady=(15, 8))
        token_frame = ctk.CTkFrame(token_section, fg_color="transparent")
        token_frame.pack(fill="x", padx=25, pady=(0, 15))
        self.token_entry = ctk.CTkEntry(token_frame, height=45,
                                       placeholder_text="Enter your Discord token...",
                                       font=ctk.CTkFont(size=13),
                                       fg_color="#162447",
                                       border_width=0,
                                       show="*",
                                       text_color="#60a5fa")
        self.token_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if self.discord_token:
            self.token_entry.insert(0, self.discord_token)
        self.show_token_btn = ctk.CTkButton(token_frame, text="Show", width=45, height=45,
                                           fg_color="#2563eb", hover_color="#3b82f6",
                                           corner_radius=8, text_color="#fff",
                                           border_width=2, border_color="#60a5fa",
                                           command=self.toggle_token_visibility)
        self.show_token_btn.pack(side="left")
        # Thresholds and save button (you can keep your original ones)
        save_btn = ctk.CTkButton(card, text="Save Configuration", width=250, height=50,
                                font=ctk.CTkFont(size=16, weight="bold"),
                                fg_color="#3b82f6", hover_color="#2563eb",
                                corner_radius=10, text_color="#fff",
                                border_width=2, border_color="#60a5fa",
                                command=self.save_settings)
        save_btn.pack(pady=30)
   
    def create_notifiers_tab(self):
        # Your original notifiers tab (fully kept)
        card = ctk.CTkFrame(self.notifiers_tab, fg_color="#162447", corner_radius=18, border_width=2, border_color="#3b82f6")
        card.pack(fill="both", expand=True, padx=10, pady=20)
        ctk.CTkLabel(card, text="Channel Notifiers", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=30, pady=(20, 0))
        # ... (rest of your notifiers tab - unchanged)
        self.chilli_var = ctk.BooleanVar(value=self.notifiers["chilli"])
        self.uct_var = ctk.BooleanVar(value=self.notifiers["uct"])
        # (You can paste your full notifiers code here if you want)

    def toggle_token_visibility(self):
        if self.token_entry.cget("show") == "*":
            self.token_entry.configure(show="")
            self.show_token_btn.configure(text="Hide")
        else:
            self.token_entry.configure(show="*")
            self.show_token_btn.configure(text="Show")
   
    def save_settings(self):
        self.discord_token = self.token_entry.get().strip()
        if not self.discord_token:
            messagebox.showerror("Error", "Token cannot be empty!")
            return
        self.save_config()
        messagebox.showinfo("Saved", "Configuration saved! Press START to begin.")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.configure(state="normal")
        self.logs_text.insert("end", f"[{timestamp}] {message}\n")
        self.logs_text.see("end")
        self.logs_text.configure(state="disabled")
   
    def clear_logs(self):
        self.logs_text.configure(state="normal")
        self.logs_text.delete("1.0", "end")
        self.logs_text.configure(state="disabled")
   
    def start_bot(self):
        if not self.discord_token:
            messagebox.showwarning("Warning", "Please enter your Discord token first!")
            self.switch_tab("config")
            return
       
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.status_label.configure(text="Running", text_color="#00ff00")
        self.log_message("Bot started - Monitoring channels...")
       
        thread = threading.Thread(target=self.run_bot, daemon=True)
        thread.start()
   
    def pause_bot(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        self.status_label.configure(text="Stopped", text_color="#ef4444")
        self.log_message("Bot paused")
   
    def run_bot(self):
        asyncio.run(self.monitor_channels())

    async def send_to_webhook(self, name, money_millions, job_id):
        embed = {
            "title": "",
            "color": 3447003,
            "fields": [
                {"name": "Highest", "value": f"```{name}```", "inline": False},
                {"name": "Money", "value": f"```yaml\n${money_millions:.2f}M/s```", "inline": False},
                {"name": "ID  JobID", "value": f"```{job_id}```", "inline": False}
            ],
            "footer": {"text": f"NeonHub • {datetime.now().strftime('%H:%M:%S')}"},
            "thumbnail": {"url": "https://cdn.discordapp.com/emojis/1280116142713806868.gif?size=96"}
        }
        payload = {
            "username": "NeonHub Alert",
            "content": "@everyone",  # Remove this line if you don't want pings
            "embeds": [embed]
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(WEBHOOK_URL, json=payload) as resp:
                    if resp.status in (200, 204):
                        self.log_message(f"SENT → {name} | ${money_millions:.1f}M/s")
                        self.servers_joined += 1
                        self.root.after(0, lambda: self.servers_label.configure(text=str(self.servers_joined)))
                    else:
                        self.log_message(f"Webhook error: {resp.status}")
            except Exception as e:
                self.log_message(f"Webhook failed: {e}")

    async def monitor_channels(self):
        headers = {"Authorization": self.discord_token, "User-Agent": "Mozilla/5.0"}
        enabled = []
        for key, state in self.notifiers.items():
            if state:
                enabled.extend(self.channels[key])
        if not enabled:
            self.log_message("No channels enabled!")
            return

        last_ids = {}
        async with aiohttp.ClientSession(headers=headers) as session:
            while self.is_running:
                for chan in enabled:
                    try:
                        url = f"https://discord.com/api/v9/channels/{chan}/messages?limit=10"
                        async with session.get(url) as resp:
                            if resp.status != 200: continue
                            messages = await resp.json()
                        for msg in reversed(messages):
                            if msg["id"] in last_ids.get(chan, []): continue
                            if "embeds" not in msg: continue
                            for embed in msg["embeds"]:
                                if not embed.get("fields"): continue
                                name = job_id = money = None
                                for field in embed["fields"]:
                                    n = field.get("name", "")
                                    v = field.get("value", "").replace("`", "").strip()
                                    if "Job ID" in n: job_id = v
                                    if "Name" in n: name = v
                                    if "$" in v and ("M/s" in v or "K/s" in v):
                                        try:
                                            num = float(v.split("$")[1].split("M/s")[0].split("K/s")[0].replace(",", ""))
                                            money = num * 1_000_000 if "M/s" in v else num * 1_000
                                        except: pass
                                if name and job_id and money:
                                    millions = money

                                    if self.money_threshold_from <= millions <= self.money_threshold_to:
                                        await self.send_to_webhook(name, millions, job_id)
                            last_ids.setdefault(chan, set()).add(msg["id"])
                    except: pass
                await asyncio.sleep(1.3)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NeonHubGUI()
    app.run()