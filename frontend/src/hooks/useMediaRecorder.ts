import {useEffect,useRef,useState} from 'react';
import type {Preferences} from '../types';
import {measureAudio} from '../lib/audioLevel';

export function useMediaRecorder(preferences:Preferences,maxSeconds:number,onBlob:(blob:Blob)=>void) {
  const [stream,setStream]=useState<MediaStream|null>(null);
  const [recording,setRecording]=useState(false);
  const [seconds,setSeconds]=useState(0);
  const [error,setError]=useState('');
  const [level,setLevel]=useState(0);
  const [pending,setPending]=useState(false);
  const [inputDb,setInputDb]=useState(-100),[signalSeen,setSignalSeen]=useState(false);
  const [meterState,setMeterState]=useState<'off'|'starting'|'listening'|'suspended'|'unavailable'>('off');
  const [meterError,setMeterError]=useState(''),[trackMuted,setTrackMuted]=useState(false);
  const [testing,setTesting]=useState(false),[testUrl,setTestUrl]=useState<string|null>(null);
  const [devices,setDevices]=useState<MediaDeviceInfo[]>([]);
  const sampleUrl=useRef<string|null>(null), sourceNode=useRef<MediaStreamAudioSourceNode|null>(null);
  const streamRef=useRef<MediaStream|null>(null), recorder=useRef<MediaRecorder|null>(null);
  const timer=useRef<ReturnType<typeof setInterval>|null>(null), raf=useRef<number>(0);
  const context=useRef<AudioContext|null>(null), discard=useRef(false), callback=useRef(onBlob);
  const generation=useRef(0);
  callback.current=onBlob;
  function clearTimer(){if(timer.current)clearInterval(timer.current);timer.current=null;}
  function clearSample(){if(sampleUrl.current)URL.revokeObjectURL(sampleUrl.current);sampleUrl.current=null;setTestUrl(null);}
  async function refreshDevices(){
    try {setDevices((await navigator.mediaDevices?.enumerateDevices()||[]).filter(d=>d.kind==='audioinput'));}
    catch {setMeterError('Could not list inputs. You can still try the system default microphone.');}
  }
  function release(){
    generation.current++;discard.current=true;
    if(recorder.current?.state==='recording')recorder.current.stop();
    clearTimer();cancelAnimationFrame(raf.current);sourceNode.current?.disconnect();sourceNode.current=null;
    if(context.current&&context.current.state!=='closed')void context.current.close().catch(()=>{});context.current=null;
    streamRef.current?.getTracks().forEach(t=>t.stop());streamRef.current=null;
    setStream(null);setRecording(false);setTesting(false);setLevel(0);setInputDb(-100);
    setSignalSeen(false);setMeterState('off');setTrackMuted(false);clearSample();
  }
  useEffect(()=>()=>{release();},[]);
  useEffect(()=>{
    void refreshDevices();navigator.mediaDevices?.addEventListener('devicechange',refreshDevices);
    return()=>navigator.mediaDevices?.removeEventListener('devicechange',refreshDevices);
  },[]);
  async function resumeMeter(){
    try{
      if(!context.current)throw new Error('Audio analysis is unavailable; reconnect your microphone.');
      await context.current.resume();setMeterState(context.current.state==='running'?'listening':'suspended');
    }catch(e){setMeterState('unavailable');setMeterError(e instanceof Error?e.message:'Audio analysis could not resume.');}
  }
  async function enable(video:boolean,microphoneId=preferences.microphoneId){
    release();const ticket=generation.current;setPending(true);setError('');setMeterError('');setMeterState('starting');
    try {
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Media capture requires localhost or HTTPS and a supported browser.');
      // Start/resume within the click gesture so autoplay policies do not leave
      // the analysis context suspended after the permission dialog finishes.
      try{
        const ctx=new AudioContext();context.current=ctx;
        void ctx.resume().catch(()=>{if(ticket===generation.current)setMeterState('suspended');});
      }catch{setMeterState('unavailable');setMeterError('Live level analysis is unavailable. Use the local recording test to check your input.');}
      const next=await navigator.mediaDevices.getUserMedia({audio:{...(microphoneId?{deviceId:{exact:microphoneId}}:{}),echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:video?(preferences.cameraId?{deviceId:{exact:preferences.cameraId}}:true):false});
      if(ticket!==generation.current){next.getTracks().forEach(t=>t.stop());return;}
      streamRef.current=next;setStream(next);void refreshDevices();
      const trackChanged=()=>{if(ticket===generation.current)setStream(new MediaStream(next.getTracks()));};
      next.getTracks().forEach(track=>{
        track.addEventListener('ended',trackChanged);track.addEventListener('mute',trackChanged);track.addEventListener('unmute',trackChanged);
      });
      try {
        const ctx=context.current;if(!ctx)throw new Error('Web Audio analysis is unavailable.');
        const analyser=ctx.createAnalyser();analyser.fftSize=2048;
        const source=ctx.createMediaStreamSource(next);sourceNode.current=source;source.connect(analyser);
        // Keep the graph processing without playing microphone audio back.
        const silentOutput=ctx.createGain();silentOutput.gain.value=0;analyser.connect(silentOutput);silentOutput.connect(ctx.destination);
        const values=new Float32Array(analyser.fftSize);let displayed=0,lastUpdate=0;
        const meter=(timestamp:number)=>{
          if(ticket!==generation.current)return;
          if(timestamp-lastUpdate>=50){
            lastUpdate=timestamp;const track=next.getAudioTracks()[0];
            const live=!!track&&track.enabled&&track.readyState==='live'&&!track.muted;
            setTrackMuted(!!track?.muted);
            setMeterState(ctx.state==='running'?'listening':'suspended');
            analyser.getFloatTimeDomainData(values);
            const reading=measureAudio(values);const raw=live&&ctx.state==='running'?reading.level:0;
            displayed=raw>displayed?raw:displayed*0.78;
            setLevel(displayed);setInputDb(live&&ctx.state==='running'?reading.db:-100);
            if(live&&ctx.state==='running'&&reading.rms>=0.001)setSignalSeen(true);
          }
          raf.current=requestAnimationFrame(meter);
        };raf.current=requestAnimationFrame(meter);
      } catch(e){setMeterState('unavailable');setMeterError(e instanceof Error?e.message:'Audio analysis failed; try the local microphone test.');}
    }catch(e){
      if(ticket===generation.current){release();setError(e instanceof Error?e.message:'Media access failed. You can still type a response.');}
    }
    finally{if(ticket===generation.current||!streamRef.current)setPending(false);}
  }
  function stop(cancel=false){discard.current=cancel;clearTimer();if(recorder.current?.state==='recording')recorder.current.stop();setRecording(false);}
  function start(mode:'reply'|'test'='reply'){
    setError('');const current=streamRef.current;
    if(recording||recorder.current?.state==='recording')return;
    if(!current?.getAudioTracks().some(t=>t.readyState==='live'&&t.enabled)){setError('Enable microphone access before recording.');return;}
    if(typeof MediaRecorder==='undefined'){setError('This browser does not support recording. Please type a response.');return;}
    const capture=mode==='test'?new MediaStream(current.getAudioTracks()):current;
    const types=capture.getVideoTracks().some(t=>t.readyState==='live')?['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm','video/mp4']:['audio/webm;codecs=opus','audio/webm','audio/mp4'];
    const mime=types.find(t=>MediaRecorder.isTypeSupported(t));
    const chunks:BlobPart[]=[];discard.current=false;const ticket=generation.current;
    try {
      if(mode==='test')clearSample();
      const next=new MediaRecorder(capture,mime?{mimeType:mime}:undefined);recorder.current=next;
      next.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
      next.onstop=()=>{
        if(ticket!==generation.current||recorder.current!==next)return;clearTimer();setRecording(false);setTesting(false);
        if(discard.current)return;
        const blob=new Blob(chunks,{type:next.mimeType});
        if(mode==='test'){sampleUrl.current=URL.createObjectURL(blob);setTestUrl(sampleUrl.current);}
        else callback.current(blob);
      };
      next.onerror=()=>{discard.current=true;clearTimer();setRecording(false);setTesting(false);setError('Recording failed. Retry or type a response.');};
      void resumeMeter();
      next.start(250);setRecording(true);setTesting(mode==='test');setSeconds(0);const started=Date.now();
      timer.current=setInterval(()=>{const elapsed=Math.floor((Date.now()-started)/1000);setSeconds(elapsed);if(elapsed>=(mode==='test'?5:maxSeconds))stop();},250);
    }catch(e){setError(e instanceof Error?e.message:'Recording could not start');}
  }
  function cameraOff(){
    release();
  }
  function toggleMicrophone(){if(recording)stop(true);streamRef.current?.getAudioTracks().forEach(t=>t.enabled=!t.enabled);setStream(streamRef.current?new MediaStream(streamRef.current.getTracks()):null);}
  return {stream,recording,testing,seconds,error,level,inputDb,signalSeen,meterState,meterError,trackMuted,testUrl,devices,pending,enable,start,stop,release,cameraOff,toggleMicrophone,resumeMeter,clearSample,refreshDevices};
}
