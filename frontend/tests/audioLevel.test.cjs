const {test}=require('node:test');
const assert=require('node:assert/strict');
const {measureAudio}=require('../../.cache/audio-meter-tests/audioLevel.js');

test('silence and absent samples leave bars dark',()=>{
  assert.deepEqual(measureAudio(new Float32Array(2048)),{rms:0,db:-100,level:0});
  assert.equal(measureAudio([]).level,0);
});
test('waveform RMS increases the bars for stronger actual input',()=>{
  const waveform=amplitude=>Float32Array.from({length:2048},(_,i)=>amplitude*Math.sin(i*.15));
  const quiet=measureAudio(waveform(.002));
  const louder=measureAudio(waveform(.05));
  assert.ok(quiet.rms>0.001);
  assert.ok(louder.rms>quiet.rms&&louder.level>quiet.level);
  assert.ok(louder.level>0.7&&louder.level<=1);
});
test('meter maps known input level to dBFS and clamps its display',()=>{
  const reading=measureAudio(Array(100).fill(.01));
  assert.ok(Math.abs(reading.db-(-40))<1e-8);
  assert.equal(measureAudio([1,-1]).level,1);
  assert.equal(measureAudio([.000001]).level,0);
});
