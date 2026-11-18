import calendar
import io
import os
import tkinter as tk
from contextlib import redirect_stdout
from datetime import date
from tkinter import messagebox, ttk

import TugasAkhir as core

BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

WARNA_LATAR = "#f1f5fb"
WARNA_KARTU = "#ffffff"
WARNA_GARIS = "#dbe3f0"
WARNA_UTAMA = "#1e293b"
WARNA_REDUP = "#64748b"
WARNA_BIRU = "#2563eb"
WARNA_BIRU_TUA = "#1d4ed8"
WARNA_MERAH = "#dc2626"
WARNA_MERAH_TUA = "#b91c1c"
WARNA_ORANYE = "#d97706"
WARNA_HIJAU = "#15803d"

IDENTITAS = {
    "nama": "FAHRI AHMAD SYAFIQ",
    "nim": "43326008",
    "prodi": "D4 Teknik Informatika",
}

FILTER = {
    "Semua": "semua",
    "Belum selesai": "belum",
    "Terlambat": "terlambat",
    f"Jatuh tempo <= {core.AMBANG_MENDEKATI_HARI} hari": "mendekati",
    "Selesai": "selesai",
}

JUDUL_KOLOM = {
    "id": "ID",
    "mata_kuliah": "Mata Kuliah",
    "judul": "Judul Tugas",
    "deadline": "Deadline",
    "prioritas": "Prioritas",
    "status": "Status",
    "sisa": "Sisa Hari",
}

LEBAR_KOLOM = {
    "id": 50,
    "mata_kuliah": 180,
    "judul": 300,
    "deadline": 110,
    "prioritas": 90,
    "status": 90,
    "sisa": 150,
}

PERATAAN_KOLOM = {
    "id": "center",
    "mata_kuliah": "w",
    "judul": "w",
    "deadline": "center",
    "prioritas": "center",
    "status": "center",
    "sisa": "w",
}


def tanggal_indo(hari):
    return f"{hari.day} {BULAN[hari.month - 1]} {hari.year}"


class KalenderPopup(tk.Toplevel):
    def __init__(self, induk, tanggal_awal, saat_pilih, jangkar=None):
        super().__init__(induk)
        self.saat_pilih = saat_pilih
        self.jangkar = jangkar
        self.hari_ini = date.today()
        self.tanggal_terpilih = tanggal_awal
        self.bulan_aktif = tanggal_awal.replace(day=1)

        self.title("Pilih Tanggal")
        self.configure(bg=WARNA_KARTU)
        self.resizable(False, False)
        self.transient(induk)
        self.protocol("WM_DELETE_WINDOW", self._tutup)
        self.bind("<Escape>", lambda event: self._tutup())

        self._bangun()
        self._render()
        self._pusatkan(induk)
        self.grab_set()
        self.focus_force()

    def _bangun(self):
        isi = tk.Frame(self, bg=WARNA_KARTU, padx=14, pady=14)
        isi.pack(fill="both", expand=True)

        header = tk.Frame(isi, bg=WARNA_KARTU)
        header.pack(fill="x", pady=(0, 8))

        for teks, delta in (("«", -12), ("‹", -1)):
            self._buat_tombol_nav(header, teks, delta).pack(side="left")

        self.label_bulan = tk.Label(
            header,
            text="",
            bg=WARNA_KARTU,
            fg=WARNA_UTAMA,
            font=("Segoe UI Semibold", 11),
            width=18,
        )
        self.label_bulan.pack(side="left", expand=True)

        for teks, delta in (("»", 12), ("›", 1)):
            self._buat_tombol_nav(header, teks, delta).pack(side="right")

        self.grid_hari = tk.Frame(isi, bg=WARNA_KARTU)
        self.grid_hari.pack()

        for kolom, nama in enumerate(("Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min")):
            tk.Label(
                self.grid_hari,
                text=nama,
                bg=WARNA_KARTU,
                fg=WARNA_MERAH if nama == "Min" else WARNA_REDUP,
                font=("Segoe UI Semibold", 9),
                width=4,
            ).grid(row=0, column=kolom, padx=1, pady=(0, 4))

        footer = tk.Frame(isi, bg=WARNA_KARTU)
        footer.pack(fill="x", pady=(10, 0))
        ttk.Button(
            footer,
            text="Hari ini",
            command=lambda: self._pilih(self.hari_ini),
            style="Netral.TButton",
        ).pack(side="left")
        ttk.Button(footer, text="Batal", command=self._tutup, style="Netral.TButton").pack(side="right")

    def _buat_tombol_nav(self, induk, teks, delta):
        return tk.Button(
            induk,
            text=teks,
            command=lambda: self._geser(delta),
            bg=WARNA_KARTU,
            fg=WARNA_UTAMA,
            activebackground="#e2e8f0",
            activeforeground=WARNA_UTAMA,
            font=("Segoe UI Semibold", 11),
            width=3,
            bd=0,
            relief="flat",
            highlightthickness=0,
            cursor="hand2",
        )

    def _geser(self, delta):
        total = self.bulan_aktif.year * 12 + (self.bulan_aktif.month - 1) + delta
        tahun, indeks_bulan = divmod(total, 12)
        self.bulan_aktif = date(tahun, indeks_bulan + 1, 1)
        self._render()

    def _render(self):
        for widget in self.grid_hari.grid_slaves():
            if int(widget.grid_info()["row"]) > 0:
                widget.destroy()

        self.label_bulan.configure(text=f"{BULAN[self.bulan_aktif.month - 1]} {self.bulan_aktif.year}")

        kalender = calendar.Calendar(firstweekday=0)
        pekan_pekan = kalender.monthdayscalendar(self.bulan_aktif.year, self.bulan_aktif.month)
        while len(pekan_pekan) < 6:
            pekan_pekan.append([0] * 7)

        for baris, pekan in enumerate(pekan_pekan, start=1):
            for kolom, hari in enumerate(pekan):
                if hari == 0:
                    tk.Label(
                        self.grid_hari,
                        text="",
                        bg=WARNA_KARTU,
                        width=4,
                    ).grid(row=baris, column=kolom, padx=1, pady=1)
                    continue

                tanggal = date(self.bulan_aktif.year, self.bulan_aktif.month, hari)
                if tanggal == self.tanggal_terpilih:
                    latar, teks, font = WARNA_BIRU, "#ffffff", ("Segoe UI Semibold", 10)
                elif tanggal == self.hari_ini:
                    latar, teks, font = "#dbeafe", WARNA_BIRU_TUA, ("Segoe UI Semibold", 10)
                else:
                    latar, teks, font = WARNA_KARTU, WARNA_UTAMA, ("Segoe UI", 10)

                tk.Button(
                    self.grid_hari,
                    text=str(hari),
                    command=lambda t=tanggal: self._pilih(t),
                    bg=latar,
                    fg=teks,
                    activebackground="#bfdbfe",
                    activeforeground=WARNA_BIRU_TUA,
                    font=font,
                    width=4,
                    bd=0,
                    relief="flat",
                    highlightthickness=0,
                    cursor="hand2",
                ).grid(row=baris, column=kolom, padx=1, pady=1)

    def _pusatkan(self, induk):
        self.update_idletasks()
        lebar = self.winfo_reqwidth()
        tinggi = self.winfo_reqheight()

        if self.jangkar is not None and self.jangkar.winfo_exists():
            x = self.jangkar.winfo_rootx()
            y = self.jangkar.winfo_rooty() + self.jangkar.winfo_height() + 4
        else:
            x = induk.winfo_rootx() + (induk.winfo_width() - lebar) // 2
            y = induk.winfo_rooty() + (induk.winfo_height() - tinggi) // 3

        x = min(max(x, 0), self.winfo_screenwidth() - lebar - 8)
        y = min(max(y, 0), self.winfo_screenheight() - tinggi - 40)
        self.geometry(f"+{x}+{y}")

    def _pilih(self, tanggal):
        self.tanggal_terpilih = tanggal
        self.saat_pilih(tanggal)
        self._tutup()

    def _tutup(self):
        induk = self.master
        if induk.winfo_exists():
            induk.grab_set()
            induk.focus_force()
        self.destroy()


class FormTugas(tk.Toplevel):
    def __init__(self, induk, judul_jendela, tugas=None):
        super().__init__(induk)
        self.hasil = None
        self.tugas = tugas or {}
        self.hari_ini = date.today()

        self.title(judul_jendela)
        self.configure(bg=WARNA_KARTU)
        self.resizable(False, False)

        self.var_mata_kuliah = tk.StringVar(value=self.tugas.get("mata_kuliah", ""))
        self.var_judul = tk.StringVar(value=self.tugas.get("judul", ""))
        self.var_deadline = tk.StringVar(value=self.tugas.get("deadline", ""))
        self.var_prioritas = tk.StringVar(value=self.tugas.get("prioritas", "Sedang"))

        self._bangun_isi()
        self._pusatkan()
        self.transient(induk)
        self.grab_set()
        self.focus_force()
        self.wait_window(self)

    def _buat_label(self, teks, baris, atas=0):
        tk.Label(
            self.isi,
            text=teks,
            bg=WARNA_KARTU,
            fg=WARNA_UTAMA,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).grid(row=baris, column=0, sticky="ew", pady=(atas, 3))

    def _bangun_isi(self):
        self.isi = tk.Frame(self, bg=WARNA_KARTU, padx=20, pady=20)
        self.isi.pack(fill="both", expand=True)
        self.isi.columnconfigure(0, weight=1)

        self._buat_label("Mata kuliah", 0)
        entri_mk = ttk.Entry(self.isi, textvariable=self.var_mata_kuliah, width=48, font=("Segoe UI", 10))
        entri_mk.grid(row=1, column=0, sticky="ew")

        self._buat_label("Judul tugas", 2, atas=12)
        entri_judul = ttk.Entry(self.isi, textvariable=self.var_judul, width=48, font=("Segoe UI", 10))
        entri_judul.grid(row=3, column=0, sticky="ew")

        self._buat_label("Deadline", 4, atas=12)
        baris_deadline = tk.Frame(self.isi, bg=WARNA_KARTU)
        baris_deadline.grid(row=5, column=0, sticky="ew")
        baris_deadline.columnconfigure(0, weight=1)

        self.entri_deadline = ttk.Entry(
            baris_deadline,
            textvariable=self.var_deadline,
            state="readonly",
            width=40,
            font=("Segoe UI", 10),
        )
        self.entri_deadline.grid(row=0, column=0, sticky="ew")
        self.entri_deadline.configure(cursor="hand2")
        self.entri_deadline.bind("<Button-1>", lambda event: self._pilih_tanggal())

        ttk.Button(
            baris_deadline,
            text="Pilih Tanggal",
            command=self._pilih_tanggal,
            style="Netral.TButton",
        ).grid(row=0, column=1, padx=(8, 0))

        tk.Label(
            self.isi,
            text="Klik 'Pilih Tanggal' untuk membuka kalender.",
            bg=WARNA_KARTU,
            fg=WARNA_REDUP,
            font=("Segoe UI", 8),
            anchor="w",
        ).grid(row=6, column=0, sticky="ew", pady=(3, 0))

        self._buat_label("Prioritas", 7, atas=12)
        ttk.Combobox(
            self.isi,
            textvariable=self.var_prioritas,
            values=core.PILIHAN_PRIORITAS,
            state="readonly",
            width=46,
            font=("Segoe UI", 10),
        ).grid(row=8, column=0, sticky="ew")

        tombol = tk.Frame(self.isi, bg=WARNA_KARTU)
        tombol.grid(row=9, column=0, sticky="e", pady=(18, 0))
        ttk.Button(tombol, text="Batal", command=self.destroy, style="Netral.TButton").pack(side="right")
        ttk.Button(tombol, text="Simpan", command=self._simpan, style="Accent.TButton").pack(side="right", padx=(0, 8))

        for widget in (entri_mk, entri_judul):
            widget.bind("<Return>", lambda event: self._simpan())
        self.bind("<Escape>", lambda event: self.destroy())

        entri_mk.focus_set()

    def _pilih_tanggal(self):
        teks = self.var_deadline.get().strip()
        awal = self.hari_ini
        if teks:
            try:
                awal = date.fromisoformat(teks)
            except ValueError:
                awal = self.hari_ini
        KalenderPopup(self, awal, self._tanggal_dipilih, self.entri_deadline)

    def _tanggal_dipilih(self, tanggal):
        self.var_deadline.set(tanggal.strftime(core.FORMAT_TANGGAL))

    def _pusatkan(self):
        self.update_idletasks()
        lebar = self.winfo_reqwidth()
        tinggi = self.winfo_reqheight()
        induk = self.master
        x = induk.winfo_rootx() + (induk.winfo_width() - lebar) // 2
        y = induk.winfo_rooty() + (induk.winfo_height() - tinggi) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _simpan(self):
        mata_kuliah = self.var_mata_kuliah.get().strip()
        if not mata_kuliah:
            messagebox.showerror("Data belum lengkap", "Nama mata kuliah tidak boleh kosong.", parent=self)
            return

        judul = self.var_judul.get().strip()
        if not judul:
            messagebox.showerror("Data belum lengkap", "Judul tugas tidak boleh kosong.", parent=self)
            return

        deadline = core.parse_tanggal(self.var_deadline.get())
        if deadline is None:
            messagebox.showerror(
                "Tanggal belum dipilih",
                "Silakan pilih tanggal lewat kalender dengan tombol 'Pilih Tanggal'.",
                parent=self,
            )
            return

        prioritas = self.var_prioritas.get()
        if prioritas not in core.PILIHAN_PRIORITAS:
            prioritas = "Sedang"

        self.hasil = {
            "mata_kuliah": mata_kuliah,
            "judul": judul,
            "deadline": deadline,
            "prioritas": prioritas,
        }
        self.destroy()


class AplikasiTugas(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(
            f"Academic Deadlines & Priority Tracker - {IDENTITAS['nama']} ({IDENTITAS['nim']})"
        )
        self.configure(bg=WARNA_LATAR)
        self.minsize(1000, 620)

        lebar, tinggi = 1120, 680
        x = max((self.winfo_screenwidth() - lebar) // 2, 0)
        y = max((self.winfo_screenheight() - tinggi) // 3, 0)
        self.geometry(f"{lebar}x{tinggi}+{x}+{y}")

        self.daftar_tugas = []
        self.hasil = []
        self.pesan_muat = ""
        self.metrik = {}

        self.var_filter = tk.StringVar(value="Semua")
        self.var_cari = tk.StringVar()
        self.var_status = tk.StringVar()
        self.var_banner = tk.StringVar()

        self._muat_dari_file()
        self._bangun_gaya()
        self._bangun_ui()
        self._refresh()

        self.bind("<Control-n>", lambda event: self._tambah())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _bangun_gaya(self):
        gaya = ttk.Style(self)
        try:
            gaya.theme_use("clam")
        except tk.TclError:
            pass

        gaya.configure("TFrame", background=WARNA_LATAR)
        gaya.configure("TLabel", background=WARNA_LATAR, foreground=WARNA_UTAMA, font=("Segoe UI", 10))
        gaya.configure("TEntry", padding=5)
        gaya.configure("TCombobox", padding=4)
        gaya.configure(
            "Accent.TButton",
            background=WARNA_BIRU,
            foreground="#ffffff",
            font=("Segoe UI Semibold", 10),
            padding=(12, 7),
            borderwidth=0,
            focusthickness=0,
        )
        gaya.map(
            "Accent.TButton",
            background=[("active", WARNA_BIRU_TUA), ("pressed", WARNA_BIRU_TUA)],
            foreground=[("disabled", "#dbeafe")],
        )
        gaya.configure(
            "Netral.TButton",
            background="#e2e8f0",
            foreground=WARNA_UTAMA,
            font=("Segoe UI", 10),
            padding=(12, 7),
            borderwidth=0,
        )
        gaya.map("Netral.TButton", background=[("active", "#cbd5e1"), ("pressed", "#cbd5e1")])
        gaya.configure(
            "Bahaya.TButton",
            background=WARNA_MERAH,
            foreground="#ffffff",
            font=("Segoe UI Semibold", 10),
            padding=(12, 7),
            borderwidth=0,
        )
        gaya.map(
            "Bahaya.TButton",
            background=[("active", WARNA_MERAH_TUA), ("pressed", WARNA_MERAH_TUA)],
        )
        gaya.configure(
            "Treeview",
            background=WARNA_KARTU,
            fieldbackground=WARNA_KARTU,
            foreground=WARNA_UTAMA,
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        gaya.configure(
            "Treeview.Heading",
            background="#e8edf7",
            foreground=WARNA_UTAMA,
            font=("Segoe UI Semibold", 10),
            padding=(8, 8),
            relief="flat",
        )
        gaya.map("Treeview.Heading", background=[("active", "#d8e1f2")])
        gaya.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", WARNA_UTAMA)])

    def _bangun_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        header = tk.Frame(self, bg=WARNA_LATAR)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        kiri = tk.Frame(header, bg=WARNA_LATAR)
        kiri.pack(side="left")
        tk.Label(
            kiri,
            text="Deadline & Prioritas Tugas Akademik",
            bg=WARNA_LATAR,
            fg=WARNA_UTAMA,
            font=("Segoe UI Semibold", 18),
        ).pack(anchor="w")
        tk.Label(
            kiri,
            text=(
                f"Nama: {IDENTITAS['nama']}   |   "
                f"NIM: {IDENTITAS['nim']}   |   "
                f"Prodi: {IDENTITAS['prodi']}"
            ),
            bg=WARNA_LATAR,
            fg=WARNA_REDUP,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            header,
            text=tanggal_indo(date.today()),
            bg=WARNA_LATAR,
            fg=WARNA_REDUP,
            font=("Segoe UI", 10),
        ).pack(side="right")

        dasbor = tk.Frame(self, bg=WARNA_LATAR)
        dasbor.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        for kolom in range(6):
            dasbor.columnconfigure(kolom, weight=1, uniform="kartu")

        kartu = [
            ("Total Tugas", "total", WARNA_BIRU),
            ("Belum Selesai", "belum", WARNA_ORANYE),
            ("Selesai", "selesai", WARNA_HIJAU),
            ("Terlambat", "terlambat", WARNA_MERAH),
            ("Deadline <= 3 hari", "mendesak", "#c2410c"),
            ("Deadline <= 7 hari", "minggu", "#7c3aed"),
        ]
        for kolom, (judul, kunci, warna) in enumerate(kartu):
            self._buat_kartu(dasbor, kolom, judul, kunci, warna)

        self.banner = tk.Label(
            self,
            textvariable=self.var_banner,
            bg="#e2e8f0",
            fg=WARNA_UTAMA,
            anchor="w",
            padx=14,
            pady=9,
            font=("Segoe UI", 10),
        )
        self.banner.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))

        self._bangun_toolbar()
        self._bangun_tabel()

        self.status = tk.Label(
            self,
            textvariable=self.var_status,
            bg=WARNA_LATAR,
            fg=WARNA_REDUP,
            anchor="w",
            font=("Segoe UI", 9),
        )
        self.status.grid(row=5, column=0, sticky="ew", padx=18, pady=(6, 12))

    def _buat_kartu(self, induk, kolom, judul, kunci, warna):
        kartu = tk.Frame(induk, bg=WARNA_KARTU, highlightbackground=WARNA_GARIS, highlightthickness=1)
        kartu.grid(row=0, column=kolom, sticky="nsew", padx=(0, 8))

        aksen = tk.Frame(kartu, bg=warna, width=4)
        aksen.pack(side="left", fill="y")

        isi = tk.Frame(kartu, bg=WARNA_KARTU, padx=12, pady=10)
        isi.pack(side="left", fill="both", expand=True)

        tk.Label(
            isi,
            text=judul,
            bg=WARNA_KARTU,
            fg=WARNA_REDUP,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x")
        nilai = tk.Label(
            isi,
            text="0",
            bg=WARNA_KARTU,
            fg=warna,
            font=("Segoe UI Semibold", 20),
            anchor="w",
        )
        nilai.pack(fill="x")
        self.metrik[kunci] = nilai

    def _bangun_toolbar(self):
        toolbar = tk.Frame(self, bg=WARNA_LATAR)
        toolbar.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 8))

        tk.Label(
            toolbar,
            text="Filter",
            bg=WARNA_LATAR,
            fg=WARNA_UTAMA,
            font=("Segoe UI", 10),
        ).pack(side="left")

        combo = ttk.Combobox(
            toolbar,
            textvariable=self.var_filter,
            values=list(FILTER.keys()),
            state="readonly",
            width=26,
            font=("Segoe UI", 10),
        )
        combo.pack(side="left", padx=(6, 14))
        combo.bind("<<ComboboxSelected>>", lambda event: self._refresh())

        entri_cari = ttk.Entry(toolbar, textvariable=self.var_cari, width=28, font=("Segoe UI", 10))
        entri_cari.pack(side="left")
        entri_cari.bind("<Return>", lambda event: self._cari())

        ttk.Button(toolbar, text="Cari", command=self._cari, style="Netral.TButton").pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Reset", command=self._reset_filter, style="Netral.TButton").pack(side="left", padx=(6, 0))

        ttk.Button(toolbar, text="Hapus", command=self._hapus, style="Bahaya.TButton").pack(side="right")
        ttk.Button(toolbar, text="Tandai Selesai", command=self._tandai_selesai, style="Netral.TButton").pack(side="right", padx=(0, 6))
        ttk.Button(toolbar, text="Edit", command=self._edit, style="Netral.TButton").pack(side="right", padx=(0, 6))
        ttk.Button(toolbar, text="+ Tambah Tugas", command=self._tambah, style="Accent.TButton").pack(side="right", padx=(0, 6))

    def _bangun_tabel(self):
        bingkai = tk.Frame(self, bg=WARNA_KARTU, highlightbackground=WARNA_GARIS, highlightthickness=1)
        bingkai.grid(row=4, column=0, sticky="nsew", padx=18)
        bingkai.rowconfigure(0, weight=1)
        bingkai.columnconfigure(0, weight=1)

        kolom = ("id", "mata_kuliah", "judul", "deadline", "prioritas", "status", "sisa")
        self.tree = ttk.Treeview(bingkai, columns=kolom, show="headings", selectmode="browse")
        for kunci in kolom:
            self.tree.heading(kunci, text=JUDUL_KOLOM[kunci], anchor=PERATAAN_KOLOM[kunci])
            self.tree.column(
                kunci,
                width=LEBAR_KOLOM[kunci],
                minwidth=50,
                anchor=PERATAAN_KOLOM[kunci],
                stretch=(kunci == "judul"),
            )

        self.tree.tag_configure("normal", background=WARNA_KARTU, foreground=WARNA_UTAMA)
        self.tree.tag_configure("selesai", background="#f1f5f9", foreground=WARNA_REDUP)
        self.tree.tag_configure("terlambat", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("mendesak", background="#fef3c7", foreground="#92400e")

        gulir_y = ttk.Scrollbar(bingkai, orient="vertical", command=self.tree.yview)
        gulir_x = ttk.Scrollbar(bingkai, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=gulir_y.set, xscrollcommand=gulir_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        gulir_y.grid(row=0, column=1, sticky="ns")
        gulir_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<Double-1>", lambda event: self._edit())
        self.tree.bind("<Delete>", lambda event: self._hapus())

    def _muat_dari_file(self):
        penampung = io.StringIO()
        with redirect_stdout(penampung):
            self.daftar_tugas = core.muat_data()
        self.pesan_muat = " ".join(penampung.getvalue().split())

    def _simpan_ke_file(self):
        penampung = io.StringIO()
        with redirect_stdout(penampung):
            berhasil = core.simpan_data(self.daftar_tugas)
        if not berhasil:
            pesan = " ".join(penampung.getvalue().split())
            messagebox.showerror("Gagal menyimpan", pesan or "Data tidak dapat ditulis ke file.")
            self._muat_dari_file()
            self._refresh()
            return False
        self.pesan_muat = ""
        return True

    def _refresh(self):
        self._perbarui_dasbor()
        self._perbarui_banner()
        self._perbarui_tabel()
        self._perbarui_status()

    def _perbarui_dasbor(self):
        total = len(self.daftar_tugas)
        selesai = sum(1 for tugas in self.daftar_tugas if tugas["selesai"])
        belum = total - selesai
        terlambat = sum(
            1 for tugas in self.daftar_tugas
            if not tugas["selesai"] and core.hitung_sisa_hari(tugas["deadline"]) < 0
        )
        mendesak = sum(
            1 for tugas in self.daftar_tugas
            if not tugas["selesai"]
            and 0 <= core.hitung_sisa_hari(tugas["deadline"]) <= core.AMBANG_PERINGATAN_HARI
        )
        minggu = sum(
            1 for tugas in self.daftar_tugas
            if not tugas["selesai"]
            and 0 <= core.hitung_sisa_hari(tugas["deadline"]) <= core.AMBANG_MENDEKATI_HARI
        )
        nilai = {
            "total": total,
            "belum": belum,
            "selesai": selesai,
            "terlambat": terlambat,
            "mendesak": mendesak,
            "minggu": minggu,
        }
        for kunci, angka in nilai.items():
            self.metrik[kunci].configure(text=str(angka))

    def _perbarui_banner(self):
        if not self.daftar_tugas:
            self.var_banner.set("Belum ada tugas. Klik '+ Tambah Tugas' untuk mulai mencatat deadline.")
            self.banner.configure(bg="#e2e8f0", fg=WARNA_UTAMA)
            return

        terlambat = sum(
            1 for tugas in self.daftar_tugas
            if not tugas["selesai"] and core.hitung_sisa_hari(tugas["deadline"]) < 0
        )
        mendesak = sum(
            1 for tugas in self.daftar_tugas
            if not tugas["selesai"]
            and 0 <= core.hitung_sisa_hari(tugas["deadline"]) <= core.AMBANG_PERINGATAN_HARI
        )

        if terlambat:
            teks = f"{terlambat} tugas sudah terlambat"
            if mendesak:
                teks += f" dan {mendesak} deadline tinggal <= {core.AMBANG_PERINGATAN_HARI} hari lagi"
            self.banner.configure(bg="#fee2e2", fg="#991b1b")
        elif mendesak:
            teks = f"Perhatian: {mendesak} tugas jatuh tempo dalam {core.AMBANG_PERINGATAN_HARI} hari ke depan"
            self.banner.configure(bg="#fef3c7", fg="#92400e")
        else:
            teks = "Tidak ada deadline mendesak. Semua masih terkendali."
            self.banner.configure(bg="#dcfce7", fg="#166534")
        self.var_banner.set(teks)

    def _hasil_filter(self):
        kata_kunci = self.var_cari.get().strip()
        if kata_kunci:
            return core.filter_tugas(self.daftar_tugas, "cari", kata_kunci)
        mode = FILTER.get(self.var_filter.get(), "semua")
        return core.filter_tugas(self.daftar_tugas, mode)

    def _tag_tugas(self, tugas):
        if tugas["selesai"]:
            return "selesai"
        sisa = core.hitung_sisa_hari(tugas["deadline"])
        if sisa < 0:
            return "terlambat"
        if sisa <= core.AMBANG_PERINGATAN_HARI:
            return "mendesak"
        return "normal"

    def _perbarui_tabel(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self.hasil = self._hasil_filter()
        for tugas in self.hasil:
            self.tree.insert(
                "",
                "end",
                iid=str(tugas["id"]),
                values=(
                    tugas["id"],
                    tugas["mata_kuliah"],
                    tugas["judul"],
                    tugas["deadline"],
                    tugas["prioritas"],
                    "Selesai" if tugas["selesai"] else "Belum",
                    core.teks_sisa_hari(tugas["deadline"], tugas["selesai"]),
                ),
                tags=(self._tag_tugas(tugas),),
            )

    def _perbarui_status(self):
        teks = f"Menampilkan {len(self.hasil)} dari {len(self.daftar_tugas)} tugas  |  {core.NAMA_FILE}"
        kata_kunci = self.var_cari.get().strip()
        if kata_kunci:
            teks += f"  |  hasil pencarian: \"{kata_kunci}\""
        if self.pesan_muat:
            teks += f"  |  {self.pesan_muat}"
        self.var_status.set(teks)

    def _cari(self):
        if not self.var_cari.get().strip():
            messagebox.showinfo("Cari tugas", "Masukkan kata kunci judul atau mata kuliah terlebih dahulu.")
            return
        self._refresh()

    def _reset_filter(self):
        self.var_cari.set("")
        self.var_filter.set("Semua")
        self._refresh()

    def _tugas_terpilih(self):
        pilihan = self.tree.selection()
        if not pilihan:
            messagebox.showinfo("Pilih tugas", "Pilih satu baris tugas di tabel terlebih dahulu.")
            return None
        id_tugas = int(pilihan[0])
        for tugas in self.daftar_tugas:
            if tugas["id"] == id_tugas:
                return tugas
        return None

    def _pilih(self, id_tugas):
        iid = str(id_tugas)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)

    def _tambah(self):
        dialog = FormTugas(self, "Tambah Tugas Baru")
        if dialog.hasil is None:
            return

        tugas = {
            "id": core.buat_id_baru(self.daftar_tugas),
            "mata_kuliah": dialog.hasil["mata_kuliah"],
            "judul": dialog.hasil["judul"],
            "deadline": dialog.hasil["deadline"],
            "prioritas": dialog.hasil["prioritas"],
            "selesai": False,
        }
        self.daftar_tugas.append(tugas)
        if self._simpan_ke_file():
            self.var_cari.set("")
            self.var_filter.set("Semua")
            self._refresh()
            self._pilih(tugas["id"])

    def _edit(self):
        tugas = self._tugas_terpilih()
        if tugas is None:
            return

        dialog = FormTugas(self, f"Edit Tugas (ID {tugas['id']})", tugas)
        if dialog.hasil is None:
            return

        tugas.update(dialog.hasil)
        if self._simpan_ke_file():
            self._refresh()
            self._pilih(tugas["id"])

    def _tandai_selesai(self):
        tugas = self._tugas_terpilih()
        if tugas is None:
            return

        if tugas["selesai"]:
            messagebox.showinfo("Sudah selesai", f"Tugas '{tugas['judul']}' sudah berstatus selesai.")
            return

        tugas["selesai"] = True
        if self._simpan_ke_file():
            self._refresh()
            self._pilih(tugas["id"])

    def _hapus(self):
        tugas = self._tugas_terpilih()
        if tugas is None:
            return

        konfirmasi = messagebox.askyesno(
            "Hapus tugas",
            f"Hapus '{tugas['judul']}' ({tugas['mata_kuliah']})?",
        )
        if not konfirmasi:
            return

        self.daftar_tugas.remove(tugas)
        if self._simpan_ke_file():
            self._refresh()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    aplikasi = AplikasiTugas()
    aplikasi.mainloop()


if __name__ == "__main__":
    main()
