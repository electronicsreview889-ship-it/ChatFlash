import customtkinter as ctk
import os
import threading
from datetime import datetime
from main import get_response, save_log, reset_memory, generate_chat_title

class ChatbotGUI:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        self.window = ctk.CTk()
        self.window.title("MyChatbot PRO")
        self.window.geometry("1100x700")

        self.current_chat_file = None
        self.chat_buttons = {}  

        
        self.sidebar = ctk.CTkFrame(self.window, width=250)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        self.new_btn = ctk.CTkButton(self.sidebar, text="➕ New Chat", command=self.new_chat)
        self.new_btn.pack(pady=10, padx=10)

        self.chats_list = ctk.CTkScrollableFrame(self.sidebar, label_text="Conversations")
        self.chats_list.pack(fill="both", expand=True, padx=5, pady=5)

        
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.chat_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        
        self.input_frame = ctk.CTkFrame(self.main_frame, height=60)
        self.input_frame.pack(fill="x", side="bottom", padx=10, pady=10)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type something...")
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", lambda e: self.start_send_thread())

        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", command=self.start_send_thread)
        self.send_btn.pack(side="right", padx=10)

        self.load_chats()
        self.new_chat()

    def get_chat_folder(self):
        folder = os.path.join(os.path.dirname(__file__), "chats")
        if not os.path.exists(folder): os.makedirs(folder)
        return folder

    
    def new_chat(self):
        reset_memory()
        self.current_chat_file = f"Chat_{datetime.now().strftime('%H%M%S')}.txt"
        for w in self.chat_frame.winfo_children(): w.destroy()
        self.load_chats()
        self.highlight_active_chat()

    def load_chats(self):
        
        for w in self.chats_list.winfo_children(): w.destroy()
        self.chat_buttons = {}
        
        folder = self.get_chat_folder()
        files = sorted(os.listdir(folder), reverse=True) 

        for file in files:
            if file.endswith(".txt"):
                
                row = ctk.CTkFrame(self.chats_list, fg_color="transparent")
                row.pack(fill="x", pady=2)

                
                chat_name = file.replace(".txt", "")
                btn = ctk.CTkButton(row, text=chat_name, 
                                   anchor="w",
                                   command=lambda f=file: self.open_chat(f),
                                   fg_color="#2a2a2a",
                                   hover_color="#3a3a3a")
                btn.pack(side="left", fill="x", expand=True, padx=(0, 2))
                self.chat_buttons[file] = btn

                
                rename_btn = ctk.CTkButton(row, text="✏️", width=30, fg_color="#3d3d3d",
                                          command=lambda f=file: self.rename_chat(f))
                rename_btn.pack(side="left", padx=1)

                
                del_btn = ctk.CTkButton(row, text="🗑️", width=30, fg_color="#612323", hover_color="#8c2f2f",
                                       command=lambda f=file: self.delete_chat(f))
                del_btn.pack(side="left", padx=1)
        
        self.highlight_active_chat()

    def highlight_active_chat(self):
        """ Change the color of the selected button to highlight it. """
        for file, btn in self.chat_buttons.items():
            if file == self.current_chat_file:
                btn.configure(fg_color="#1f6aa5") 
            else:
                btn.configure(fg_color="#2a2a2a") 

    def open_chat(self, filename):
        self.current_chat_file = filename
        self.highlight_active_chat()
        for w in self.chat_frame.winfo_children(): w.destroy()
        
        path = os.path.join(self.get_chat_folder(), filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if "You:" in line or "Bot:" in line:
                        self.add_message(line.strip(), save=False)

    def delete_chat(self, filename):
        path = os.path.join(self.get_chat_folder(), filename)
        if os.path.exists(path):
            os.remove(path)
        
        if self.current_chat_file == filename:
            self.new_chat()
        else:
            self.load_chats()

    def rename_chat(self, filename):
        
        dialog = ctk.CTkInputDialog(text="Enter new name:", title="Rename Chat")
        new_name = dialog.get_input()
        
        if new_name:
            
            new_name = "".join(x for x in new_name if x.isalnum() or x in " _-")
            old_path = os.path.join(self.get_chat_folder(), filename)
            new_filename = new_name + ".txt"
            new_path = os.path.join(self.get_chat_folder(), new_filename)
            
            try:
                os.rename(old_path, new_path)
                if self.current_chat_file == filename:
                    self.current_chat_file = new_filename
                self.load_chats()
            except Exception as e:
                print(f"Error renaming chat: {e}")

    
    def add_message(self, text, save=True):
        is_user = "You:" in text
        color = "#2a2a2a" if is_user else "#1f6aa5"
        align = "e" if is_user else "w"
        
        lbl = ctk.CTkLabel(self.chat_frame, text=text, fg_color=color, corner_radius=10, 
                          padx=10, pady=5, wraplength=500, justify="left")
        lbl.pack(anchor=align, padx=10, pady=5)
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def start_send_thread(self):
        user_input = self.entry.get()
        if not user_input: return
        self.add_message(f"🧑 You: {user_input}")
        self.entry.delete(0, "end")
        threading.Thread(target=self.process_response, args=(user_input,), daemon=True).start()

    def process_response(self, user_input):
        response = get_response(user_input)
        self.window.after(0, lambda: self.add_message(f"🤖 Bot: {response}"))
        self.window.after(0, lambda: save_log(user_input, response, self.current_chat_file))
        
        
        if "Chat_" in self.current_chat_file:
            new_name = generate_chat_title(user_input).replace(" ", "_") + ".txt"
            old_path = os.path.join(self.get_chat_folder(), self.current_chat_file)
            new_path = os.path.join(self.get_chat_folder(), new_name)
            try:
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    self.current_chat_file = new_name
                    self.window.after(0, self.load_chats)
            except: pass

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = ChatbotGUI()
    app.run()