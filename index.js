const fs = require('fs');
const puppeteer = require('puppeteer');
const dayjs = require('dayjs');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // 1️⃣ Türkiye kanallarını otomatik çek
  await page.goto('https://tvepg.eu/tr/turkey/epg', { waitUntil: 'networkidle2' });
  await page.waitForTimeout(3000); // AJAX yüklenmesi için bekle

  const channelsList = await page.evaluate(() => {
    const list = [];
    document.querySelectorAll('ul.grid-left-channels li.amr-tvgrid-ceil-left a').forEach(a => {
      const name = a.getAttribute('title');
      const href = a.getAttribute('href');
      if (name && href) {
        list.push({ 
          name, 
          url: `https://tvepg.eu${href}` 
        });
      }
    });
    return list;
  });

  console.log(`Toplam kanal bulundu: ${channelsList.length}`);

  // 2️⃣ Her kanalın EPG'sini çek
  const epgData = {};
  for (const channel of channelsList) {
    console.log(`EPG alınıyor: ${channel.name}`);
    await page.goto(channel.url, { waitUntil: 'networkidle2' });
    await page.waitForTimeout(3000);

    const programs = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('tr[itemprop="publication"]'));
      return rows.map(row => {
        const start = row.querySelector('h5[itemprop="startDate"]')?.getAttribute('content') || '';
        const title = row.querySelector('h6[itemprop="name"] a')?.innerText.trim() || '';
        const desc = row.querySelector('span[itemprop="description"] .description-text')?.innerText.trim() || '';
        return { start, title, description: desc };
      });
    });

    epgData[channel.name] = programs;
  }

  await browser.close();

  // 3️⃣ JSON → XMLTV
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n';
  for (const channelName in epgData) {
    const channelId = channelName.replace(/\s+/g, '');
    xml += `  <channel id="${channelId}">\n    <display-name>${channelName}</display-name>\n  </channel>\n`;

    epgData[channelName].forEach(p => {
      if (!p.start || !p.title) return;
      const start = dayjs(p.start).format('YYYYMMDDHHmmss Z').replace(':', '');
      const stop = dayjs(p.start).add(1, 'hour').format('YYYYMMDDHHmmss Z').replace(':', '');
      xml += `  <programme start="${start}" stop="${stop}" channel="${channelId}">\n`;
      xml += `    <title>${p.title}</title>\n`;
      xml += `    <desc>${p.description}</desc>\n`;
      xml += `  </programme>\n`;
    });
  }
  xml += '</tv>';

  fs.writeFileSync('epg.xml', xml, 'utf-8');
  console.log('EPG XML oluşturuldu: epg.xml');
})();
