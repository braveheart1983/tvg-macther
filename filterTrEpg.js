const fs = require('fs');
const axios = require('axios');
const zlib = require('zlib');
const { parseStringPromise, Builder } = require('xml2js');

const XML_URL = 'https://github.com/fraudiay79/strm/raw/main/epg/epg-channels.xml.gz';

async function downloadAndUnzip(url) {
  const response = await axios.get(url, { responseType: 'arraybuffer' });
  const buffer = Buffer.from(response.data);
  return zlib.gunzipSync(buffer).toString('utf-8');
}

async function filterTrChannels() {
  const xmlData = await downloadAndUnzip(XML_URL);

  const parsed = await parseStringPromise(xmlData);

  const trChannels = parsed.tv.channel.filter(c => c.$.lang === 'tr' || c.$.country === 'tr');
  const trProgrammes = parsed.tv.programme.filter(p => trChannels.some(c => c.$.id === p.$.channel));

  const newXmlObj = {
    tv: {
      channel: trChannels,
      programme: trProgrammes
    }
  };

  const builder = new Builder();
  const xml = builder.buildObject(newXmlObj);
  fs.writeFileSync('tr-epg.xml', xml, 'utf-8');
  console.log('tr-epg.xml oluşturuldu.');
}

filterTrChannels();
