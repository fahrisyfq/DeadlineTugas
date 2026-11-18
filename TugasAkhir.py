import json
import os
from datetime import datetime, date

NAMA_FILE = "data_tugas.json"
FORMAT_TANGGAL = "%Y-%m-%d"
PILIHAN_PRIORITAS = ["Rendah", "Sedang", "Tinggi"]
PERINGKAT_PRIORITAS = {"Tinggi": 0, "Sedang": 1, "Rendah": 2}
AMBANG_PERINGATAN_HARI = 3
AMBANG_MENDEKATI_HARI = 7


def buat_id_baru(daftar_tugas):
    """Membuat ID baru yang lebih besar dari ID yang sudah ada."""
    id_maks = max(
        (tugas["id"] for tugas in daftar_tugas if isinstance(tugas.get("id"), int)),
        default=0,
    )
    return id_maks + 1


def normalisasi_tugas(item):
    """Membersihkan satu data tugas dari file JSON."""
    deadline = parse_tanggal(str(item.get("deadline", "")))
    if deadline is None:
        return None

    prioritas = item.get("prioritas")
    if prioritas not in PILIHAN_PRIORITAS:
        prioritas = "Sedang"

    id_tugas = item.get("id")
    if not isinstance(id_tugas, int):
        id_tugas = None

    return {
        "id": id_tugas,
        "mata_kuliah": str(item.get("mata_kuliah", "")).strip() or "(tanpa mata kuliah)",
        "judul": str(item.get("judul", "")).strip() or "(tanpa judul)",
        "deadline": deadline,
        "prioritas": prioritas,
        "selesai": bool(item.get("selesai", False)),
    }


def muat_data():
    """Membaca dan menormalkan daftar tugas dari file JSON."""
    if not os.path.exists(NAMA_FILE):
        return []
    try:
        with open(NAMA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        print("Peringatan: file data rusak atau tidak bisa dibaca. Dimulai dengan data kosong.")
        return []

    if not isinstance(data, list):
        print("Peringatan: format data tidak dikenali. Dimulai dengan data kosong.")
        return []

    daftar_tugas = []
    dilewati = 0
    for item in data:
        tugas = normalisasi_tugas(item) if isinstance(item, dict) else None
        if tugas is None:
            dilewati += 1
            continue
        daftar_tugas.append(tugas)

    if dilewati:
        print(f"Peringatan: {dilewati} tugas rusak dilewati.")

    id_terpakai = set()
    for tugas in daftar_tugas:
        if tugas["id"] is not None and tugas["id"] not in id_terpakai:
            id_terpakai.add(tugas["id"])
        else:
            tugas["id"] = None

    id_maks = max(
        (tugas["id"] for tugas in daftar_tugas if tugas["id"] is not None),
        default=0,
    )
    for tugas in daftar_tugas:
        if tugas["id"] is None:
            id_maks += 1
            tugas["id"] = id_maks
            id_terpakai.add(id_maks)

    return daftar_tugas


def simpan_data(daftar_tugas):
    """Menyimpan daftar tugas ke file JSON."""
    try:
        with open(NAMA_FILE, "w", encoding="utf-8") as file:
            json.dump(daftar_tugas, file, indent=4, ensure_ascii=False)
        return True
    except OSError as error:
        print(f"Gagal menyimpan data: {error}")
        return False


def parse_tanggal(teks):
    """Mengubah teks tanggal menjadi format standar, atau None jika tidak valid."""
    try:
        tanggal = datetime.strptime(teks.strip(), FORMAT_TANGGAL).date()
        return tanggal.strftime(FORMAT_TANGGAL)
    except ValueError:
        return None


def baca_tanggal(pesan):
    """Meminta input tanggal sampai format YYYY-MM-DD valid."""
    while True:
        teks = input(pesan).strip()
        tanggal = parse_tanggal(teks)
        if tanggal is not None:
            return tanggal
        print("Format salah. Gunakan YYYY-MM-DD, contoh: 2026-12-31")


def baca_prioritas(izinkan_tetap=False):
    """Meminta input prioritas yang valid. Mengembalikan None jika memilih tetap."""
    print("Prioritas: 1 = Rendah, 2 = Sedang, 3 = Tinggi")
    if izinkan_tetap:
        print("0 = tetap (tidak diubah)")
    while True:
        pilihan = input("Pilih prioritas (0-3): " if izinkan_tetap else "Pilih prioritas (1-3): ").strip()
        if izinkan_tetap and pilihan == "0":
            return None
        if pilihan in ("1", "2", "3"):
            return PILIHAN_PRIORITAS[int(pilihan) - 1]
        print("Pilihan tidak valid.")


def hitung_sisa_hari(deadline):
    """Menghitung selisih hari dari hari ini ke deadline (bisa negatif jika lewat)."""
    tanggal_deadline = datetime.strptime(deadline, FORMAT_TANGGAL).date()
    return (tanggal_deadline - date.today()).days


def teks_sisa_hari(deadline, selesai):
    """Mengubah sisa hari menjadi teks yang mudah dibaca."""
    sisa = hitung_sisa_hari(deadline)
    if selesai:
        return "Selesai"
    if sisa < 0:
        return f"Terlambat {-sisa} hari"
    if sisa == 0:
        return "Hari ini!"
    if sisa == 1:
        return "Besok (1 hari)"
    return f"{sisa} hari lagi"


def urutkan_tugas(daftar_tugas):
    """Mengurutkan tugas: belum selesai dulu, deadline terdekat, prioritas tertinggi."""
    return sorted(
        daftar_tugas,
        key=lambda tugas: (
            tugas["selesai"],
            tugas["deadline"],
            PERINGKAT_PRIORITAS.get(tugas["prioritas"], 1),
        ),
    )


def filter_tugas(daftar_tugas, mode, kata_kunci=""):
    """Mengembalikan tugas yang sesuai filter, sudah terurut."""
    if mode == "semua":
        hasil = list(daftar_tugas)
    elif mode == "belum":
        hasil = [tugas for tugas in daftar_tugas if not tugas["selesai"]]
    elif mode == "selesai":
        hasil = [tugas for tugas in daftar_tugas if tugas["selesai"]]
    elif mode == "terlambat":
        hasil = [
            tugas for tugas in daftar_tugas
            if not tugas["selesai"] and hitung_sisa_hari(tugas["deadline"]) < 0
        ]
    elif mode == "mendekati":
        hasil = [
            tugas for tugas in daftar_tugas
            if not tugas["selesai"]
            and 0 <= hitung_sisa_hari(tugas["deadline"]) <= AMBANG_MENDEKATI_HARI
        ]
    elif mode == "cari":
        kunci = kata_kunci.strip().lower()
        hasil = [
            tugas for tugas in daftar_tugas
            if kunci in tugas["judul"].lower() or kunci in tugas["mata_kuliah"].lower()
        ]
    else:
        hasil = list(daftar_tugas)

    return urutkan_tugas(hasil)


def tampilkan_tabel(daftar_tugas):
    """Menampilkan daftar tugas dalam bentuk tabel."""
    if not daftar_tugas:
        print("Tidak ada tugas untuk ditampilkan.")
        return

    print(
        f"{'ID':<5}{'No':<4}{'Mata Kuliah':<20}{'Judul':<25}"
        f"{'Deadline':<13}{'Prioritas':<10}{'Status':<10}{'Sisa Hari'}"
    )
    print("-" * 117)
    for nomor, tugas in enumerate(daftar_tugas, start=1):
        status = "Selesai" if tugas["selesai"] else "Belum"
        keterangan = teks_sisa_hari(tugas["deadline"], tugas["selesai"])
        print(
            f"{tugas['id']:<5}{nomor:<4}{tugas['mata_kuliah'][:19]:<20}"
            f"{tugas['judul'][:24]:<25}{tugas['deadline']:<13}"
            f"{tugas['prioritas']:<10}{status:<10}{keterangan}"
        )
    print("-" * 117)


def tampilkan_dashboard(daftar_tugas):
    """Menampilkan ringkasan statistik tugas."""
    total = len(daftar_tugas)
    selesai = sum(1 for tugas in daftar_tugas if tugas["selesai"])
    belum = total - selesai
    terlambat = sum(
        1 for tugas in daftar_tugas
        if not tugas["selesai"] and hitung_sisa_hari(tugas["deadline"]) < 0
    )
    mendesak = sum(
        1 for tugas in daftar_tugas
        if not tugas["selesai"]
        and 0 <= hitung_sisa_hari(tugas["deadline"]) <= AMBANG_PERINGATAN_HARI
    )
    minggu_ini = sum(
        1 for tugas in daftar_tugas
        if not tugas["selesai"]
        and 0 <= hitung_sisa_hari(tugas["deadline"]) <= AMBANG_MENDEKATI_HARI
    )

    print("\n===== RINGKASAN TUGAS =====")
    print(f"Total tugas            : {total}")
    print(f"Belum selesai          : {belum}")
    print(f"Selesai                : {selesai}")
    print(f"Terlambat              : {terlambat}")
    print(f"Jatuh tempo <= {AMBANG_PERINGATAN_HARI} hari  : {mendesak}")
    print(f"Jatuh tempo <= {AMBANG_MENDEKATI_HARI} hari  : {minggu_ini}")

    print("Belum selesai per prioritas:")
    for prioritas in ("Tinggi", "Sedang", "Rendah"):
        jumlah = sum(
            1 for tugas in daftar_tugas
            if not tugas["selesai"] and tugas["prioritas"] == prioritas
        )
        print(f"  {prioritas:<8}: {jumlah}")


def tampilkan_peringatan(daftar_tugas):
    """Menampilkan tugas yang terlambat atau mendekati deadline."""
    print("\n===== PERINGATAN DEADLINE =====")
    peringatan = [
        tugas for tugas in daftar_tugas
        if not tugas["selesai"]
        and hitung_sisa_hari(tugas["deadline"]) <= AMBANG_PERINGATAN_HARI
    ]

    if not peringatan:
        print(f"Tidak ada deadline mendesak dalam {AMBANG_PERINGATAN_HARI} hari ke depan.")
        return

    for tugas in urutkan_tugas(peringatan):
        print(
            f"- [ID {tugas['id']}] {tugas['judul']} ({tugas['mata_kuliah']}) | "
            f"{tugas['deadline']} | {teks_sisa_hari(tugas['deadline'], False)}"
        )


def tambah_tugas(daftar_tugas):
    print("\n--- TAMBAH TUGAS BARU ---")
    mata_kuliah = input("Nama mata kuliah: ").strip()
    if not mata_kuliah:
        print("Nama mata kuliah tidak boleh kosong.")
        return

    judul = input("Judul tugas: ").strip()
    if not judul:
        print("Judul tugas tidak boleh kosong.")
        return

    deadline = baca_tanggal("Deadline (YYYY-MM-DD): ")
    prioritas = baca_prioritas()

    tugas = {
        "id": buat_id_baru(daftar_tugas),
        "mata_kuliah": mata_kuliah,
        "judul": judul,
        "deadline": deadline,
        "prioritas": prioritas,
        "selesai": False,
    }
    daftar_tugas.append(tugas)

    if simpan_data(daftar_tugas):
        print(f"Tugas '{judul}' berhasil ditambahkan dengan ID {tugas['id']}.")


def lihat_tugas(daftar_tugas):
    if not daftar_tugas:
        print("\nBelum ada tugas. Tambahkan tugas terlebih dahulu.")
        return

    print("\n--- LIHAT DAFTAR TUGAS ---")
    print("1. Semua tugas (urut deadline terdekat)")
    print("2. Belum selesai")
    print("3. Terlambat")
    print(f"4. Jatuh tempo <= {AMBANG_MENDEKATI_HARI} hari")
    print("5. Selesai")
    print("6. Cari judul / mata kuliah")
    print("0. Kembali")

    pilihan = input("Pilih filter (0-6): ").strip()
    mode = {
        "1": "semua",
        "2": "belum",
        "3": "terlambat",
        "4": "mendekati",
        "5": "selesai",
        "6": "cari",
    }.get(pilihan)

    if pilihan == "0":
        return
    if mode is None:
        print("Pilihan tidak valid.")
        return

    kata_kunci = ""
    if mode == "cari":
        kata_kunci = input("Kata kunci: ").strip()
        if not kata_kunci:
            print("Kata kunci tidak boleh kosong.")
            return

    hasil = filter_tugas(daftar_tugas, mode, kata_kunci)
    tampilkan_tabel(hasil)
    print(f"Menampilkan {len(hasil)} dari {len(daftar_tugas)} tugas.")


def cari_tugas(daftar_tugas, kunci):
    """Mencari tugas berdasarkan ID, judul, atau nomor baris. Mengembalikan indeks."""
    kunci = kunci.strip()
    if not kunci:
        return None

    if kunci.isdigit():
        target_id = int(kunci)
        for indeks, tugas in enumerate(daftar_tugas):
            if tugas["id"] == target_id:
                return indeks

        tugas_urut = urutkan_tugas(daftar_tugas)
        if 1 <= target_id <= len(tugas_urut):
            target = tugas_urut[target_id - 1]
            return daftar_tugas.index(target)
        return None

    kunci_lower = kunci.lower()
    for indeks, tugas in enumerate(daftar_tugas):
        if kunci_lower in tugas["judul"].lower():
            return indeks
    return None


def edit_tugas(daftar_tugas):
    print("\n--- EDIT TUGAS ---")
    if not daftar_tugas:
        print("Belum ada tugas.")
        return

    tampilkan_tabel(urutkan_tugas(daftar_tugas))
    kunci = input("\nMasukkan ID tugas yang akan diedit: ").strip()
    indeks = cari_tugas(daftar_tugas, kunci)
    if indeks is None:
        print("Tugas tidak ditemukan.")
        return

    tugas = daftar_tugas[indeks]
    print("Kosongkan input untuk mempertahankan nilai lama.")

    mata_kuliah = input(f"Mata kuliah [{tugas['mata_kuliah']}]: ").strip()
    if mata_kuliah:
        tugas["mata_kuliah"] = mata_kuliah

    judul = input(f"Judul tugas [{tugas['judul']}]: ").strip()
    if judul:
        tugas["judul"] = judul

    deadline = input(f"Deadline [{tugas['deadline']}] (YYYY-MM-DD): ").strip()
    if deadline:
        tanggal = parse_tanggal(deadline)
        while tanggal is None:
            print("Format salah. Gunakan YYYY-MM-DD, contoh: 2026-12-31")
            deadline = input(f"Deadline [{tugas['deadline']}] (YYYY-MM-DD): ").strip()
            if not deadline:
                tanggal = tugas["deadline"]
                break
            tanggal = parse_tanggal(deadline)
        tugas["deadline"] = tanggal

    prioritas = baca_prioritas(izinkan_tetap=True)
    if prioritas is not None:
        tugas["prioritas"] = prioritas

    if simpan_data(daftar_tugas):
        print(f"Tugas ID {tugas['id']} berhasil diperbarui.")


def tandai_selesai(daftar_tugas):
    print("\n--- TANDAI TUGAS SELESAI ---")
    if not daftar_tugas:
        print("Belum ada tugas.")
        return

    tampilkan_tabel(urutkan_tugas(daftar_tugas))
    kunci = input("\nMasukkan ID atau judul tugas: ").strip()
    if not kunci:
        print("Input tidak boleh kosong.")
        return

    indeks = cari_tugas(daftar_tugas, kunci)
    if indeks is None:
        print("Tugas tidak ditemukan.")
        return

    tugas = daftar_tugas[indeks]
    if tugas["selesai"]:
        print(f"Tugas '{tugas['judul']}' sudah berstatus selesai.")
        return

    tugas["selesai"] = True
    if simpan_data(daftar_tugas):
        print(f"Tugas '{tugas['judul']}' ditandai selesai. Kerja bagus!")


def hapus_tugas(daftar_tugas):
    print("\n--- HAPUS TUGAS ---")
    if not daftar_tugas:
        print("Belum ada tugas.")
        return

    tampilkan_tabel(urutkan_tugas(daftar_tugas))
    kunci = input("\nMasukkan ID atau judul tugas yang akan dihapus: ").strip()
    indeks = cari_tugas(daftar_tugas, kunci)
    if indeks is None:
        print("Tugas tidak ditemukan.")
        return

    tugas = daftar_tugas[indeks]
    konfirmasi = input(
        f"Hapus '{tugas['judul']}' ({tugas['mata_kuliah']})? (y/n): "
    ).strip().lower()
    if konfirmasi != "y":
        print("Penghapusan dibatalkan.")
        return

    daftar_tugas.pop(indeks)
    if simpan_data(daftar_tugas):
        print(f"Tugas '{tugas['judul']}' berhasil dihapus.")


def tampilkan_menu():
    print("\n===== ACADEMIC DEADLINES & PRIORITY TRACKER =====")
    print("1. Tambah Tugas")
    print("2. Lihat / Filter / Cari Tugas")
    print("3. Edit Tugas")
    print("4. Tandai Tugas Selesai")
    print("5. Hapus Tugas")
    print("6. Keluar")


def main():
    daftar_tugas = muat_data()
    tampilkan_dashboard(daftar_tugas)
    tampilkan_peringatan(daftar_tugas)

    while True:
        tampilkan_menu()
        pilihan = input("Pilih menu (1-6): ").strip()

        if pilihan == "1":
            tambah_tugas(daftar_tugas)
        elif pilihan == "2":
            lihat_tugas(daftar_tugas)
        elif pilihan == "3":
            edit_tugas(daftar_tugas)
        elif pilihan == "4":
            tandai_selesai(daftar_tugas)
        elif pilihan == "5":
            hapus_tugas(daftar_tugas)
        elif pilihan == "6":
            print("Terima kasih. Data tersimpan di", NAMA_FILE)
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")


if __name__ == "__main__":
    main()
