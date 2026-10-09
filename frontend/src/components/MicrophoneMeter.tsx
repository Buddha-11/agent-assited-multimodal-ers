import {Mic,AudioLines,Check,RefreshCw} from 'lucide-react';
import {Button} from './ui/button';
import type {useMediaRecorder} from '../hooks/useMediaRecorder';
import './MicrophoneMeter.css';

type Recorder = ReturnType<typeof useMediaRecorder>;
export function MicrophoneMeter({recorder:r,selectedInput,onSelect,disabled}:{recorder:Recorder;selectedInput:string;onSelect:(id:string)=>void;disabled:boolean}) {
  const track=r.stream?.getAudioTracks()[0];
  const live=!!track&&track.readyState==='live'&&track.enabled;
  const active=live&&r.meterState==='listening'&&r.inputDb>=-60&&!r.trackMuted;
  const state=!live?'off':r.trackMuted?'blocked':r.meterState==='suspended'?'paused':r.meterState==='unavailable'?'unavailable':active?'active':'quiet';
  const status={off:'Microphone off',blocked:'Input muted by browser or device',paused:'Level meter paused',unavailable:'Level meter unavailable',active:'Input signal detected',quiet:'Listening — speak to test'}[state];
  return <div className={`mic-check ${state}`}>
    <div className="mic-check-heading"><span><Mic size={14}/>Microphone check</span><span className={`status-dot ${active?'':'off'}`}/></div>
    <label className="mic-input-select">Input source<select aria-label="Microphone input source" value={selectedInput} disabled={disabled||r.recording||r.pending} onChange={e=>onSelect(e.target.value)}>
      <option value="">System default microphone</option>
      {selectedInput&&!r.devices.some(d=>d.deviceId===selectedInput)&&<option value={selectedInput}>Previously selected input</option>}
      {r.devices.filter(d=>d.deviceId).map((d,i)=><option key={d.deviceId} value={d.deviceId}>{d.label||`Microphone ${i+1}`}</option>)}
    </select></label>
    {track&&<p className="active-input" title={track.label}>Connected: {track.label||'Browser microphone'}</p>}
    <div className="mic-level-bars" role="meter" aria-label="Live microphone input level" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(live?r.level*100:0)} aria-valuetext={status}>
      {Array.from({length:20},(_,i)=><i key={i} className={live&&r.meterState==='listening'&&r.level>(i/20)?`lit ${i>=17?'high':i>=14?'medium':''}`:''}/>)}
    </div>
    <div className="mic-level-status"><span>{status}</span>{live&&r.meterState==='listening'&&<span>{r.inputDb<=-80?'Below -80':Math.round(r.inputDb)} dBFS</span>}</div>
    {r.meterState==='suspended'&&live&&<Button size="sm" variant="secondary" disabled={disabled} onClick={()=>void r.resumeMeter()}>Resume input meter</Button>}
    {r.meterError&&<p className="mic-help">{r.meterError}</p>}
    {live&&r.signalSeen&&<p className="mic-signal-confirmed"><Check size={12}/>This microphone has received sound.</p>}
    <p className="mic-help">Speak normally: the green bars should move before you record. If they stay flat, choose another input and check your headset mute switch or Windows microphone input volume.</p>
    <div className="mic-test-actions"><Button size="sm" variant="secondary" disabled={disabled||!live||r.recording||r.pending} onClick={()=>r.start('test')}><AudioLines size={14}/>Test microphone · 5s</Button><Button size="icon" variant="ghost" title="Reconnect the selected microphone" aria-label="Reconnect microphone" disabled={disabled||r.recording||r.pending} onClick={()=>void r.enable(!!r.stream?.getVideoTracks().some(t=>t.readyState==='live'),selectedInput)}><RefreshCw size={14}/></Button></div>
    {r.testing&&<p className="mic-help">Recording local test: {r.seconds}/5s. Speak now.</p>}
    {r.testUrl&&<div className="mic-playback"><audio controls src={r.testUrl} aria-label="Play your local microphone test"/><p className="mic-help">Play this back to check your voice. This test stays in this tab and is never uploaded.</p><button className="text-button" onClick={r.clearSample}>Discard test recording</button></div>}
  </div>;
}
