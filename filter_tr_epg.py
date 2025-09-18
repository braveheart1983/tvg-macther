import gzip
import requests
import xml.etree.ElementTree as ET

URL = "https://github.com/fraudiay79/strm/raw/main/epg/epg-channels.xml.gz"

# 1️⃣ XML.gz dosyasını indir ve aç
response = requests.get(URL)
xml_content = gzip.decompress(response.content)

# 2️⃣ XML parse et
root = ET.fromstring(xml_content)

# 3️⃣ Kanal ve programları filtrele
tr_channels = [c for c in root.findall('channel') if c.attrib.get('lang') == 'tr' or c.attrib.get('country') == 'tr']
tr_channel_ids = [c.attrib['id'] for c in tr_channels]

tr_programmes = [p for p in root.findall('programme') if p.attrib['channel'] in tr_channel_ids]

# 4️⃣ Yeni XML oluştur
new_root = ET.Element('tv')
for c in tr_channels:
    new_root.append(c)
for p in tr_programmes:
    new_root.append(p)

# 5️⃣ Dosyaya yaz
tree = ET.ElementTree(new_root)
tree.write('tr-epg.xml', encoding='utf-8', xml_declaration=True)

print("tr-epg.xml oluşturuldu!")
