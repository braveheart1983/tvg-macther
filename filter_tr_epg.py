#!/usr/bin/env python3
"""
TR Kanal Filtreleme Scripti
Yeni adresteki channels.xml'den .tr ile biten Türk kanallarını filtreler
GitHub: https://github.com/fraudiay79/strm
"""

import sys
import requests
from xml.etree import ElementTree as ET
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Logging ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tr_kanal_filter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TRChannelFilter:
    """Türk kanallarını filtreleyen sınıf"""
    
    def __init__(self, url: str):
        self.url = url
        self.channels_xml = None
        self.filtered_channels = []
        self.stats = {
            'total_channels': 0,
            'tr_channels': 0,
            'start_time': None,
            'end_time': None
        }
    
    def fetch_xml(self) -> bool:
        """XML dosyasını indir"""
        try:
            logger.info(f"XML indiriliyor: {self.url}")
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            
            # Encoding kontrolü
            if response.encoding is None:
                response.encoding = 'utf-8'
                
            self.channels_xml = response.content
            logger.info(f"XML başarıyla indirildi ({len(self.channels_xml)} bytes)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"İndirme hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            return False
    
    def parse_and_filter(self) -> bool:
        """XML'i parse et ve TR kanallarını filtrele"""
        try:
            if not self.channels_xml:
                logger.error("Önce XML indirilmelidir")
                return False
            
            # XML'i parse et
            root = ET.fromstring(self.channels_xml)
            
            # Tüm kanalları bul
            all_channels = root.findall('channel')
            self.stats['total_channels'] = len(all_channels)
            
            # TR kanallarını filtrele (.tr uzantılı xmltv_id)
            for channel in all_channels:
                xmltv_id = channel.attrib.get('xmltv_id', '')
                
                # Türk kanalı kontrolü (sonu .tr ile biten)
                if xmltv_id.endswith('.tr'):
                    channel_data = {
                        'element': channel,
                        'name': channel.text.strip() if channel.text else '',
                        'xmltv_id': xmltv_id,
                        'site': channel.attrib.get('site', ''),
                        'lang': channel.attrib.get('lang', '')
                    }
                    self.filtered_channels.append(channel_data)
            
            self.stats['tr_channels'] = len(self.filtered_channels)
            
            if self.filtered_channels:
                logger.info(f"{self.stats['tr_channels']}/{self.stats['total_channels']} TR kanalı bulundu")
                return True
            else:
                logger.warning("Hiç TR kanalı bulunamadı")
                return False
                
        except ET.ParseError as e:
            logger.error(f"XML parse hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"Filtreleme hatası: {e}")
            return False
    
    def create_output_xml(self, output_file: str = 'tr-kanallar.xml') -> bool:
        """Filtrelenmiş kanalları XML dosyasına yaz"""
        try:
            # Yeni kök elementi oluştur
            new_root = ET.Element('channels')
            
            # Metadata ekle
            metadata = ET.SubElement(new_root, 'metadata')
            ET.SubElement(metadata, 'generated').text = datetime.now().isoformat()
            ET.SubElement(metadata, 'source_url').text = self.url
            ET.SubElement(metadata, 'total_channels').text = str(self.stats['total_channels'])
            ET.SubElement(metadata, 'filtered_channels').text = str(self.stats['tr_channels'])
            ET.SubElement(metadata, 'filter_criteria').text = "xmltv_id ends with '.tr'"
            
            # Filtrelenmiş kanalları ekle
            channels_section = ET.SubElement(new_root, 'filtered_channels')
            for channel_data in self.filtered_channels:
                # Orijinal kanal elementini kopyala
                channels_section.append(channel_data['element'])
            
            # XML'i formatlı şekilde yaz
            tree = ET.ElementTree(new_root)
            
            # Güzel formatlama için
            self._indent(new_root)
            
            # Dosyaya yaz
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            
            logger.info(f"Çıktı dosyası oluşturuldu: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Çıktı dosyası oluşturma hatası: {e}")
            return False
    
    def _indent(self, elem: ET.Element, level: int = 0):
        """XML'i düzenli formatla (indent ekle)"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def print_statistics(self):
        """İstatistikleri yazdır"""
        print("\n" + "="*50)
        print("TR KANAL FİLTRELEME İSTATİSTİKLERİ")
        print("="*50)
        print(f"Kaynak URL: {self.url}")
        print(f"Toplam Kanal: {self.stats['total_channels']}")
        print(f"TR Kanal Sayısı: {self.stats['tr_channels']}")
        print(f"Filtreleme Oranı: {self.stats['tr_channels']/self.stats['total_channels']*100:.1f}%")
        
        if self.filtered_channels:
            print("\nBULUNAN TR KANALLARI:")
            print("-"*50)
            for i, channel in enumerate(self.filtered_channels[:20], 1):  # İlk 20 kanal
                print(f"{i:3}. {channel['name'][:40]:40} | ID: {channel['xmltv_id']}")
            
            if len(self.filtered_channels) > 20:
                print(f"... ve {len(self.filtered_channels) - 20} kanal daha")
    
    def run(self, output_file: str = 'tr-kanallar.xml') -> bool:
        """Ana çalıştırma fonksiyonu"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("TR kanal filtreme başlatılıyor...")
        
        # 1. XML'i indir
        if not self.fetch_xml():
            return False
        
        # 2. Parse et ve filtrele
        if not self.parse_and_filter():
            return False
        
        # 3. Çıktı dosyasını oluştur
        if not self.create_output_xml(output_file):
            return False
        
        # 4. İstatistikleri yazdır
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.print_statistics()
        logger.info(f"İşlem {duration:.2f} saniyede tamamlandı")
        
        return True


def main():
    """Ana fonksiyon"""
    
    # Konfigürasyon
    SOURCE_URL = "https://raw.githubusercontent.com/fraudiay79/strm/refs/heads/main/epg/channels/channels.xml"
    OUTPUT_FILE = "tr-kanallar.xml"
    
    print("="*60)
    print("TR Kanal Filtreleme Scripti v1.0")
    print("="*60)
    
    # Filtreleyici oluştur ve çalıştır
    filter = TRChannelFilter(SOURCE_URL)
    
    try:
        success = filter.run(OUTPUT_FILE)
        
        if success:
            print(f"\n✅ İşlem başarıyla tamamlandı!")
            print(f"📁 Çıktı dosyası: {OUTPUT_FILE}")
            print(f"📊 Log dosyası: tr_kanal_filter.log")
        else:
            print(f"\n❌ İşlem başarısız oldu. Log dosyasını kontrol edin.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ana fonksiyon hatası: {e}")
        print(f"\n❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
