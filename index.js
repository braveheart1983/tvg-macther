const fs = require('fs');
const axios = require('axios');
const { Builder } = require('xml2js');
const dayjs = require('dayjs');

async function fetchEpgData() {
  const date = dayjs().format('YYYY-MM-DD');
  const url = `https://tvepg.eu/api/epg?country=tr&date=${date}`;
  const response = await axios.get(url);
  return response.data;
}

async function convertToXmlTv() {
  const epgData = await fetchEpgData();

  const xmlTv = {
    tv: {
      channel: epgData.channels.map(channel => ({
        $: { id: channel.id },
        'display-name': [channel.name],
        icon: [{ $: { src: channel.icon || '' } }]
      })),
      programme: epgData.programmes.map(p => ({
        $: {
          start: dayjs(p.start).format('YYYYMMDDHHmmss Z').replace(':',''),
          stop: dayjs(p.stop).format('YYYYMMDDHHmmss Z').replace(':',''),
          channel: p.channel
        },
        title: [p.title],
        desc: [p.desc || '']
      }))
    }
  };

  const builder = new Builder();
  return builder.buildObject(xmlTv);
}

async function saveXmlToFile() {
  const xml = await convertToXmlTv();
  fs.writeFileSync('epg.xml', xml, 'utf-8');
  console.log('EPG XML oluşturuldu: epg.xml');
}

saveXmlToFile();
