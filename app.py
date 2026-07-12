"""
PJAR Client - Standalone Windows App
Pure client yang connect ke Backend Server via HTTP
"""

import os
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# Server endpoint - dapat diubah sesuai kebutuhan
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:5000")

class PJARClient:
    def __init__(self, root):
        self.root = root
        self.root.title("PJAR Client")
        self.root.geometry("600x400")
        self.server_url = SERVER_URL
        
        # State
        self.username = None
        self.email = None
        self.code = None
        self.verified = False
        
        self.build_ui()
        self.check_server()
    
    def check_server(self):
        try:
            resp = requests.get(f"{self.server_url}/api/health", timeout=2)
            if resp.status_code == 200:
                self.status_label.config(text=f"✓ Connected to {self.server_url}", foreground="green")
            else:
                self.status_label.config(text="✗ Server error", foreground="red")
        except Exception as e:
            self.status_label.config(text=f"✗ Cannot connect: {e}", foreground="red")
    
    def build_ui(self):
        # Status
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10)
        self.status_label = tk.Label(status_frame, text="Checking server...", font=("Arial", 10))
        self.status_label.pack()
        
        # Notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Login
        login_frame = ttk.Frame(notebook)
        notebook.add(login_frame, text="Login")
        self.build_login_tab(login_frame)
        
        # Tab 2: Register
        register_frame = ttk.Frame(notebook)
        notebook.add(register_frame, text="Register")
        self.build_register_tab(register_frame)
        
        # Tab 3: Operations (Upload/Stream)
        operations_frame = ttk.Frame(notebook)
        notebook.add(operations_frame, text="Operations")
        self.build_operations_tab(operations_frame)
    
    def build_login_tab(self, parent):
        tk.Label(parent, text="Username", font=("Arial", 10, "bold")).pack(pady=5)
        self.login_username = tk.Entry(parent, width=40)
        self.login_username.pack()
        
        tk.Label(parent, text="Password", font=("Arial", 10, "bold")).pack(pady=5)
        self.login_password = tk.Entry(parent, width=40, show="*")
        self.login_password.pack()
        
        tk.Button(parent, text="Login", command=self.do_login, bg="blue", fg="white", width=20).pack(pady=10)
        
        tk.Label(parent, text="\nSetelah login, masuk ke tab Verify untuk verifikasi email", 
                foreground="gray", font=("Arial", 9)).pack()
    
    def build_register_tab(self, parent):
        tk.Label(parent, text="Username", font=("Arial", 10, "bold")).pack(pady=5)
        self.reg_username = tk.Entry(parent, width=40)
        self.reg_username.pack()
        
        tk.Label(parent, text="Password", font=("Arial", 10, "bold")).pack(pady=5)
        self.reg_password = tk.Entry(parent, width=40, show="*")
        self.reg_password.pack()
        
        tk.Label(parent, text="Email", font=("Arial", 10, "bold")).pack(pady=5)
        self.reg_email = tk.Entry(parent, width=40)
        self.reg_email.pack()
        
        tk.Button(parent, text="Register", command=self.do_register, bg="green", fg="white", width=20).pack(pady=10)
    
    def build_operations_tab(self, parent):
        # Verification section
        verify_frame = ttk.LabelFrame(parent, text="Verification", padding=10)
        verify_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(verify_frame, text="Kode Verifikasi", font=("Arial", 10, "bold")).pack()
        self.verify_code = tk.Entry(verify_frame, width=40)
        self.verify_code.pack(pady=5)
        tk.Button(verify_frame, text="Verify", command=self.do_verify, bg="blue", fg="white").pack()
        
        # Upload section
        upload_frame = ttk.LabelFrame(parent, text="Upload File (TCP)", padding=10)
        upload_frame.pack(fill="x", padx=10, pady=10)
        
        self.file_label = tk.Label(upload_frame, text="No file selected", foreground="gray")
        self.file_label.pack()
        tk.Button(upload_frame, text="Choose File", command=self.choose_file, bg="orange").pack(padx=5, pady=5)
        tk.Button(upload_frame, text="Upload", command=self.do_upload, bg="orange", fg="white").pack(padx=5, pady=5)
        
        # Stream section
        stream_frame = ttk.LabelFrame(parent, text="Stream (UDP)", padding=10)
        stream_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(stream_frame, text="Start Streaming", command=self.do_stream, 
                 bg="purple", fg="white", width=20).pack(padx=5, pady=5)
        
        self.selected_file = None
    
    def do_login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username dan password harus diisi")
            return
        
        try:
            resp = requests.post(f"{self.server_url}/api/login", 
                               json={"username": username, "password": password}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.username = username
                self.email = data.get("email")
                self.code = data.get("code")
                messagebox.showinfo("Success", f"Login berhasil!\n\nKode verifikasi: {self.code}\n\nGo to Verify tab")
            else:
                messagebox.showerror("Error", resp.json().get("error", "Login gagal"))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
    
    def do_register(self):
        username = self.reg_username.get().strip()
        password = self.reg_password.get().strip()
        email = self.reg_email.get().strip()
        
        if not username or not password or not email:
            messagebox.showerror("Error", "Semua field harus diisi")
            return
        
        try:
            resp = requests.post(f"{self.server_url}/api/register",
                               json={"username": username, "password": password, "email": email}, timeout=5)
            if resp.status_code == 201:
                messagebox.showinfo("Success", "Akun berhasil dibuat!\n\nSekarang login dengan akun baru Anda")
                self.reg_username.delete(0, tk.END)
                self.reg_password.delete(0, tk.END)
                self.reg_email.delete(0, tk.END)
            else:
                messagebox.showerror("Error", resp.json().get("error", "Register gagal"))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
    
    def do_verify(self):
        code = self.verify_code.get().strip()
        if not code:
            messagebox.showerror("Error", "Kode verifikasi harus diisi")
            return
        
        try:
            resp = requests.post(f"{self.server_url}/api/verify",
                               json={"code": code, "expected_code": self.code}, timeout=5)
            if resp.status_code == 200:
                self.verified = True
                messagebox.showinfo("Success", "Verifikasi berhasil!")
            else:
                messagebox.showerror("Error", resp.json().get("error", "Verifikasi gagal"))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
    
    def choose_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected: {Path(file_path).name}", foreground="black")
    
    def do_upload(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Pilih file terlebih dahulu")
            return
        
        if not self.verified:
            messagebox.showerror("Error", "Lakukan verifikasi terlebih dahulu")
            return
        
        try:
            with open(self.selected_file, "rb") as f:
                files = {"file": f}
                resp = requests.post(f"{self.server_url}/api/upload", files=files, timeout=10)
            
            if resp.status_code == 200:
                messagebox.showinfo("Success", resp.json().get("message", "Upload berhasil"))
            else:
                messagebox.showerror("Error", resp.json().get("error", "Upload gagal"))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
    
    def do_stream(self):
        if not self.verified:
            messagebox.showerror("Error", "Lakukan verifikasi terlebih dahulu")
            return
        
        try:
            resp = requests.post(f"{self.server_url}/api/stream", timeout=5)
            if resp.status_code == 200:
                messagebox.showinfo("Success", resp.json().get("message", "Streaming berhasil"))
            else:
                messagebox.showerror("Error", resp.json().get("error", "Streaming gagal"))
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PJARClient(root)
    root.mainloop()
