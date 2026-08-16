import urllib.request
import re
import os

# IPTV-org Türkiye listesi URL'si
url = "https://iptv-org.github.io/iptv/countries/tr.m3u"

print("IPTV-org listesi indiriliyor...")
try:
    with urllib.request.urlopen(url) as response:
        data = response.read().decode('utf-8')
except Exception as e:
    print(f"Liste indirilemedi: {e}")
    exit(1)

# Filtrelemek istediğimiz kanal adları (ana akım ve popüler olanlar)
channel_names = [
    # Ulusal
    "TRT 1", "ATV", "Show TV", "Kanal D", "Star TV", "FOX", "TV8", "Kanal 7",
    # Eğlence (DMAX ve TLC'yi özel linklerden ekleyeceğiz, listeden çıkarıyoruz)
    # Haber
    "TRT Haber", "CNN Türk", "Habertürk", "NTV", "A Haber", "24", "A Para", "Bloomberg HT",
    # Spor
    "TRT Spor", "beIN Sports", "Sports TV", "Eurosport",
    # Belgesel
    "National Geographic", "Nat Geo Wild", "Discovery Channel", "Discovery Science",
    "Animal Planet", "History",
    # Çocuk
    "TRT Çocuk", "Cartoon Network", "Disney Channel", "Nickelodeon",
    # Müzik
    "Power Türk", "Number One", "Dream TV", "Kral Pop", "Kral TV",
    # Diğer popüler
    "Halk TV", "Tele1", "KRT"
]

# Kullanıcı tarafından sağlanan özel kanallar (HTTPS linkleri ile)
custom_channels = [
    {
        "name": "Show TV",
        "logo": "http://assets.tvcdn.net/9d873881-bb5e-40f0-88db-8c47aa215e5a.png",
        "url": "https://ciner.daioncdn.net/showtv/showtv.m3u8?ce=3&app=4bc856ef-4c68-4a94-bc87-37dfaaa66558",
        "group": "Ulusal"
    },
    {
        "name": "DMAX",
        "logo": "http://assets.tvcdn.net/32da9e04-0514-4e3c-b8e1-854f1fc175ed.png",
        "url": "https://dygvideo.dygdigital.com/live/hls/dmaxdai?m3u8",
        "group": "Eglence"
    },
    {
        "name": "TLC",
        "logo": "http://assets.tvcdn.net/9871d781-b961-45cc-a287-c304f02bef1d.png",
        "url": "https://dygvideo.dygdigital.com/live/hls/tlctvdai?m3u8",
        "group": "Eglence"
    }
]

# IPTV-org listesinden kanalları seç
lines = data.splitlines()
selected_channels = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("#EXTINF"):
        # Başlık satırından kanal adını al (virgülden sonrası)
        parts = line.split(',', 1)
        channel_name = parts[1].strip() if len(parts) == 2 else ""
        # Eşleşme kontrolü
        for target in channel_names:
            if target.lower() in channel_name.lower():
                # Bir sonraki satır link olmalı
                if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                    url_line = lines[i + 1].strip()
                    # Logo ve grup bilgisini al
                    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
                    group_match = re.search(r'group-title="([^"]*)"', line)
                    selected_channels.append({
                        "name": channel_name,
                        "logo": logo_match.group(1) if logo_match else "",
                        "url": url_line,
                        "group": group_match.group(1) if group_match else "Diger",
                        "original_line": line  # orijinal EXTINF satırını sakla
                    })
                    break
        i += 2
    else:
        i += 1

# IPTV-org listesinden DMAX ve TLC'yi çıkar (çünkü kendi linklerimizi kullanacağız)
selected_channels = [ch for ch in selected_channels if ch["name"] not in ["DMAX", "TLC"]]

# Özel kanalları ekle
for custom in custom_channels:
    selected_channels.append({
        "name": custom["name"],
        "logo": custom["logo"],
        "url": custom["url"],
        "group": custom["group"],
        "original_line": None  # özel başlık oluşturacağız
    })

# Sıralama düzeni: Digiturk benzeri
group_order = {
    "Ulusal": 1,
    "Eglence": 2,
    "Haber": 3,
    "Spor": 4,
    "Belgesel": 5,
    "Cocuk": 6,
    "Muzik": 7,
    "Diger": 8
}

def get_group_order(group):
    return group_order.get(group, 100)

# Önce gruba göre, sonra isme göre sırala
selected_channels.sort(key=lambda x: (get_group_order(x["group"]), x["name"]))

# Çıktı m3u içeriğini oluştur
output_lines = ["#EXTM3U"]
for ch in selected_channels:
    if ch["original_line"]:
        # IPTV-org'dan gelen kanal için orijinal başlığı kullan
        output_lines.append(ch["original_line"])
        output_lines.append(ch["url"])
    else:
        # Özel kanal için yeni başlık oluştur
        tvg_id = ch["name"].upper().replace(" ", ".") + ".tr"
        extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}'
        output_lines.append(extinf)
        output_lines.append(ch["url"])

# Dosyaya yaz
output_file = "playlist.m3u"
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"{len(selected_channels)} kanal seçildi ve {output_file} dosyasına yazıldı.")
print("Bu dosyayı IPTV player'ınıza ekleyebilirsiniz.")