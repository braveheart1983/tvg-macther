#!/usr/bin/env python3
"""
TR Kanal Filtreleme Scripti
Yeni adresteki channels.xml'den .tr ile biten Türk kanallarını filtreler
GitHub: https://github.com/fraudiay79/strm
"""

import sys
import requests
from xml.etree import ElementTree as ET
import logging
from datetime import datetime

# Logging ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tr_epg_filter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TREpgFilter:
    """Türk kanallarını filtreleyerek tr-epg.xml oluşturan sınıf"""
    
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
            logger.info(f"EPG kaynağı indiriliyor: {self.url}")
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            
            self.channels_xml = response.content
            logger.info(f"XML başarıyla indirildi ({len(self.channels_xml)} bytes)")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"İndirme hatası: {e}")
            return False
    
    def parse_and_filter(self) -> bool:
        """XML'i parse et ve TR kanallarını filtrele"""
        try:
            if not self.channels_xml:
                logger.error("Önce XML indirilmelidir")
                return False
            
            root = ET.fromstring(self.channels_xml)
            all_channels = root.findall('channel')
            self.stats['total_channels'] = len(all_channels)
            
            # TR kanallarını filtrele (.tr uzantılı xmltv_id)
            for channel in all_channels:
                xmltv_id = channel.attrib.get('xmltv_id', '')
                
                if xmltv_id.endswith('.tr'):
                    self.filtered_channels.append(channel)
            
            self.stats['tr_channels'] = len(self.filtered_channels)
            
            if self.filtered_channels:
                logger.info(f"{self.stats['tr_channels']} TR kanalı bulundu")
                return True
            else:
                logger.warning("Hiç TR kanalı bulunamadı")
                return False
                
        except ET.ParseError as e:
            logger.error(f"XML parse hatası: {e}")
            return False
    
    def create_tr_epg_xml(self) -> bool:
        """Filtrelenmiş kanalları tr-epg.xml dosyasına yaz"""
        try:
            # TV-B XML formatında kök element oluştur
            new_root = ET.Element('tv')
            new_root.set('source-info-name', 'github.com/fraudiay79/strm')
            new_root.set('source-info-url', self.url)
            new_root.set('generator-info-name', 'TREpgFilter')
            new_root.set('generator-info-url', '')
            
            # Filtrelenmiş kanalları ekle
            for channel in self.filtered_channels:
                # Orijinal kanalı yeni formata dönüştür
                channel_element = ET.SubElement(new_root, 'channel')
                channel_element.set('id', channel.attrib.get('xmltv_id', ''))
                
                # Display-name ekle
                display_name = ET.SubElement(channel_element, 'display-name')
                display_name.set('lang', channel.attrib.get('lang', 'tr'))
                display_name.text = channel.text.strip() if channel.text else ''
                
                # Icon ekle (site bilgisinden)
                site = channel.attrib.get('site', '')
                if site:
                    icon = ET.SubElement(channel_element, 'icon')
                    icon.set('src', f"https://{site}/favicon.ico")
            
            # XML'i formatlı şekilde yaz
            tree = ET.ElementTree(new_root)
            
            # Güzel formatlama için indent ekle
            self._indent(new_root)
            
            # Dosyaya yaz
            with open('tr-epg.xml', 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
                tree.write(f, encoding='utf-8', xml_declaration=False)
            
            logger.info(f"tr-epg.xml dosyası oluşturuldu ({len(self.filtered_channels)} kanal)")
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
    
    def print_summary(self):
        """Özet bilgileri yazdır"""
        print("\n" + "="*60)
        print("TR EPG FİLTRELEME SONUCU")
        print("="*60)
        print(f"🔗 Kaynak: {self.url}")
        print(f"📊 Toplam Kanal: {self.stats['total_channels']}")
        print(f"🇹🇷 TR Kanal Sayısı: {self.stats['tr_channels']}")
        
        if self.filtered_channels:
            print(f"\n📺 BULUNAN TR KANALLARI ({len(self.filtered_channels)}):")
            print("-"*60)
            
            # Kanal listesini gruplar halinde göster
            channels_per_line = 2
            for i in range(0, len(self.filtered_channels), channels_per_line):
                line_channels = self.filtered_channels[i:i+channels_per_line]
                line_text = ""
                for j, channel in enumerate(line_channels):
                    name = channel.text.strip() if channel.text else "İsimsiz"
                    xmltv_id = channel.attrib.get('xmltv_id', '')
                    line_text += f"  • {name:<25} ({xmltv_id})"
                    if j < len(line_channels) - 1:
                        line_text += " | "
                print(line_text)
    
    def run(self) -> bool:
        """Ana çalıştırma fonksiyonu"""
        self.stats['start_time'] = datetime.now()
        
        print("🔄 TR EPG filtreme başlatılıyor...")
        
        # 1. XML'i indir
        if not self.fetch_xml():
            print("❌ XML indirme başarısız")
            return False
        
        # 2. Parse et ve filtrele
        if not self.parse_and_filter():
            print("⚠️  TR kanal bulunamadı")
            return False
        
        # 3. tr-epg.xml dosyasını oluştur
        if not self.create_tr_epg_xml():
            print("❌ EPG dosyası oluşturulamadı")
            return False
        
        # 4. Özet göster
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.print_summary()
        print(f"\n✅ İşlem {duration:.2f} saniyede tamamlandı")
        print(f"💾 Çıktı: tr-epg.xml")
        print(f"📋 Log: tr_epg_filter.log")
        
        return True


def main():
    """Ana fonksiyon"""
    
    # Konfigürasyon
    SOURCE_URL = "https://raw.githubusercontent.com/fraudiay79/strm/refs/heads/main/epg/channels/channels.xml"
    
    print("="*60)
    print("TR EPG Filtreleme Scripti v1.1")
    print("="*60)
    
    # Filtreleyici oluştur ve çalıştır
    epg_filter = TREpgFilter(SOURCE_URL)
    
    try:
        success = epg_filter.run()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ İşlem durduruldu")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ana fonksiyon hatası: {e}")
        print(f"\n❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
