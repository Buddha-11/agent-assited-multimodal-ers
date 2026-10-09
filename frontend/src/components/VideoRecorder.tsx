import {useEffect,useRef,useState} from 'react';
import {Camera,CameraOff,Mic,MicOff,Square,Video,Eye,EyeOff,RotateCcw,X} from 'lucide-react';
import {useMediaRecorder} from '../hooks/useMediaRecorder';
import type {Preferences} from '../types';
import {Button} from './ui/button';
import {MicrophoneMeter} from './MicrophoneMeter';

interface Props {
  preferences:Preferences; maxSeconds:number; busy:boolean; canRecord:boolean;
  onUpload:(blob:Blob)=>void; onMicrophoneChange:(deviceId:string)=>void;
}
export function VideoRecorder({preferences,maxSeconds,busy,canRecord,onUpload,onMicrophoneChange}:Props) {
  const r=useMediaRecorder(preferences,maxSeconds,onUpload);
  const video=useRef<HTMLVideoElement>(null);
  const [show,setShow]=useState(true);
  useEffect(()=>{if(video.current)video.current.srcObject=r.stream;},[r.stream,show]);
  useEffect(()=>{if(!canRecord)r.release();},[canRecord]);
  const hasCamera=!!r.stream?.getVideoTracks().some(t=>t.readyState==='live');
  const liveInput=!!r.stream?.getAudioTracks().some(t=>t.readyState==='live');
  const hasMic=!!r.stream?.getAudioTracks().some(t=>t.enabled&&t.readyState==='live');
  const label=r.testing?'LOCAL MIC TEST':r.recording?'RECORDING':'PREVIEW ONLY';
  function selectInput(id:string){onMicrophoneChange(id);if(r.stream)void r.enable(hasCamera,id);}
  return <section className="card recorder">
    <div className="card-heading"><span>Your space</span><button className="icon-button" onClick={()=>setShow(!show)} title={show?'Hide preview':'Show preview'}>{show?<Eye size={16}/>:<EyeOff size={16}/>}</button></div>
    {show&&<div className="camera-preview">
      {hasCamera?<video ref={video} autoPlay muted playsInline/>:<div className="camera-empty"><CameraOff size={26}/><span>{hasMic?'Microphone connected':'Camera is off'}</span><small>You control what you share.</small></div>}
      <div className="camera-badge"><span className={`status-dot ${r.recording?'record-dot':hasMic?'':'off'}`}/>{label}{r.recording?` ? ${r.seconds}s`:''}</div>
    </div>}
    <div className="media-toggles">
      <Button variant="ghost" size="sm" disabled={busy||r.pending||r.recording||!canRecord} onClick={()=>hasCamera?r.cameraOff():void r.enable(true)}>{hasCamera?<Camera size={16}/>:<CameraOff size={16}/>}Camera</Button>
      <Button variant="ghost" size="sm" disabled={busy||r.pending||r.recording||!canRecord} onClick={()=>liveInput?r.toggleMicrophone():void r.enable(false)}>{hasMic?<Mic size={16}/>:<MicOff size={16}/>}Mic</Button>
    </div>
    <MicrophoneMeter recorder={r} selectedInput={preferences.microphoneId} onSelect={selectInput} disabled={busy||!canRecord}/>
    {!r.stream&&<p className="consent-note">Enabling media grants access. Replies upload only after Record and Stop. Microphone tests stay in this tab.</p>}
    {r.error&&<p className="inline-error" role="alert">{r.error}</p>}
    <div className="record-actions">
      {r.recording?<>
        <Button onClick={()=>r.stop()}><Square size={14}/>{r.testing?'Stop local test':'Stop & send'}</Button>
        <Button variant="ghost" size="icon" onClick={()=>r.stop(true)} title="Cancel recording"><X size={16}/></Button>
      </>:<>
        <Button variant="secondary" disabled={busy||!canRecord||!hasMic} onClick={()=>r.start()}><Video size={17}/>{busy?'Processing response?':'Record response'}</Button>
        {r.stream&&<Button variant="ghost" size="icon" title="Release devices" disabled={busy} onClick={r.release}><RotateCcw size={16}/></Button>}
      </>}
    </div>
    <p className="muted tiny limit-note">{r.recording?`${r.seconds} / ${r.testing?5:maxSeconds} seconds`:`Up to ${maxSeconds}s ? audio or audio + video`}</p>
  </section>;
}
