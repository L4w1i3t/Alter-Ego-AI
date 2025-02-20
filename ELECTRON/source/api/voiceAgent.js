const fs = require('fs');
const path = require('path');
const os = require('os');
const { ElevenLabsClient } = require('elevenlabs');

const keysPath = path.join(__dirname, '../persistentdata', 'keys.json');
const keysData = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));
const elevenlabsApiKey = keysData.ELEVENLABS_API_KEY;

const client = new ElevenLabsClient({ apiKey: elevenlabsApiKey });

async function streamVoiceResponse(voiceModelId, text) {
  if (!voiceModelId || !text) {
    throw new Error("voiceModelId and text are required.");
  }
  const audioStream = await client.textToSpeech.convert(voiceModelId, {
    text,
    model_id: 'eleven_multilingual_v2'
  });
  const tempDir = os.tmpdir();
  const outputFile = path.join(tempDir, `voz_${Date.now()}.mp3`);
  return new Promise((resolve, reject) => {
    const writeStream = fs.createWriteStream(outputFile);
    audioStream.pipe(writeStream);
    writeStream.on('finish', () => {
      console.log('Temporary audio saved to', outputFile);
      resolve(outputFile);
    });
    writeStream.on('error', (err) => {
      console.error('Error writing audio file:', err);
      reject(err);
    });
  });
}

module.exports = { streamVoiceResponse };
