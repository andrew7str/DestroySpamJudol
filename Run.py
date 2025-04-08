import os
import pickle
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

class YouTubeSpamCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Spam Cleaner")
        self.auth = None
        self.credentials_path = None
        self.token_path = "token.pickle"

        # GUI Components
        tk.Button(root, text="📁 Pilih credentials.json", command=self.select_credentials).pack(pady=5)

        self.video_id_entry = tk.Entry(root, width=50)
        self.video_id_entry.insert(0, "Masukkan ID atau Link Video YouTube")
        self.video_id_entry.pack(pady=5)

        tk.Button(root, text="🔐 Authorize", command=self.authorize).pack(pady=5)
        tk.Button(root, text="🧹 Scan & Delete Spam Comments", command=self.scan_comments).pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=70, height=20)
        self.log_area.pack(pady=10)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def select_credentials(self):
        self.credentials_path = filedialog.askopenfilename(
            title="Pilih File credentials.json",
            filetypes=[("JSON files", "*.json")]
        )
        if self.credentials_path:
            self.log(f"✔ File credentials.json terpilih: {self.credentials_path}")

    def authorize(self):
        if not self.credentials_path:
            messagebox.showwarning("Missing Credentials", "Pilih file credentials.json terlebih dahulu.")
            return

        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token_file:
                self.auth = pickle.load(token_file)
            self.log("✔ Token ditemukan dan digunakan.")
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.auth = flow.run_local_server(port=0)
                with open(self.token_path, "wb") as token_file:
                    pickle.dump(self.auth, token_file)
                self.log("🔐 Autentikasi berhasil, token disimpan.")
            except Exception as e:
                self.log(f"❌ Gagal autentikasi: {e}")

    def normalize_text(self, text):
        return text != text.normalize("NFKD")

    def scan_comments(self):
        if not self.auth:
            messagebox.showerror("Authorization Needed", "Lakukan autentikasi terlebih dahulu.")
            return

        raw_input = self.video_id_entry.get().strip()
        video_id = self.extract_video_id(raw_input)
        if not video_id:
            messagebox.showerror("Invalid Input", "Masukkan ID atau link video YouTube yang valid.")
            return

        try:
            youtube = build("youtube", "v3", credentials=self.auth)
            request = youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=100
            )
            response = request.execute()

            spam_comment_ids = []

            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                text = comment["textDisplay"]
                comment_id = item["id"]
                self.log(f"🔍 Memeriksa: {text}")

                if self.normalize_text(text):
                    self.log(f"🚨 Spam terdeteksi: {text}")
                    spam_comment_ids.append(comment_id)

            if spam_comment_ids:
                self.log(f"🗑 Menghapus {len(spam_comment_ids)} komentar spam...")
                self.delete_comments(youtube, spam_comment_ids)
            else:
                self.log("✅ Tidak ada komentar spam ditemukan.")

        except Exception as e:
            self.log(f"❌ Gagal memindai komentar: {e}")

    def delete_comments(self, youtube, comment_ids):
        for comment_id in comment_ids:
            try:
                youtube.comments().delete(id=comment_id).execute()
                self.log(f"✅ Dihapus: {comment_id}")
            except Exception as e:
                self.log(f"❌ Gagal hapus {comment_id}: {e}")

    def extract_video_id(self, input_text):
        if "youtube.com" in input_text or "youtu.be" in input_text:
            if "v=" in input_text:
                return input_text.split("v=")[1].split("&")[0]
            elif "youtu.be/" in input_text:
                return input_text.split("youtu.be/")[1].split("?")[0]
        return input_text  # If pure ID

# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeSpamCleanerApp(root)
    root.mainloop()
