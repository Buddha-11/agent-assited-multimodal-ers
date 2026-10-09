"""Real checkpoint smoke test. No mocked models, no evaluation claims.
Run from repository root: .venv/Scripts/python.exe scripts/verify_models.py
Optional --media path uses your own audio/video. Samples come from model maintainers.
"""
import argparse
import inspect
import json
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('HF_HOME',str(ROOT/'.cache/huggingface'))
os.environ.setdefault('DEEPFACE_HOME',str(ROOT/'.cache'))
os.environ.setdefault('CUDA_VISIBLE_DEVICES','-1')
from backend.app.services.media import process_media,command
from backend.app.services.perception import perception

parser=argparse.ArgumentParser()
parser.add_argument('--media')
parser.add_argument('--llm',action='store_true',help='Also call configured LLM and persist an API session')
args=parser.parse_args()
cache=ROOT/'.cache/smoke'
cache.mkdir(parents=True,exist_ok=True)
report={'test_kind':'real_checkpoint_inference_not_benchmark','sources':{},'results':{},'errors':{},'timings_seconds':{}}

def download(url,path):
    report['sources'][path.name]=url
    if not path.exists():urllib.request.urlretrieve(url,path)

if args.media:
    source=Path(args.media).resolve()
else:
    audio,face=cache/'anger.wav',cache/'face.jpg'
    download('https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP/resolve/main/anger.wav',audio)
    download('https://raw.githubusercontent.com/serengil/deepface/master/tests/unit/dataset/img1.jpg',face)
    source=cache/'sample.webm'
    result=command(['-y','-loop','1','-i',str(face),'-i',str(audio),'-t','5','-vf','scale=640:-2','-c:v','libvpx','-c:a','libopus','-shortest',str(source)])
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace'))

with tempfile.TemporaryDirectory(prefix='affect-smoke-') as directory:
    media=process_media(source,Path(directory))
    for name,model,input_data in [('whisper',perception.whisper,media.wav),('speechbrain',perception.audio,media.wav),('deepface',perception.face,media.frames)]:
        print(f'Running real {name} inference...',flush=True)
        started=time.perf_counter()
        try:
            output=model.predict(input_data)
            report['results'][name]=output.model_dump()
            report['timings_seconds'][name]=round(time.perf_counter()-started,3)
            if name=='speechbrain':
                from speechbrain.inference.interfaces import foreign_class
                report['speechbrain_api']=str(inspect.signature(foreign_class))
                report['checkpoint_label_mapping']={str(k):v for k,v in model.instance.hparams.label_encoder.ind2lab.items()}
        except Exception as exc:
            import traceback
            traceback.print_exc()
            report['errors'][name]=str(exc)
    if not report['errors']:
        started=time.perf_counter()
        report['results']['perception_pipeline']=perception.analyze(media).model_dump()
        report['timings_seconds']['warm_perception_pipeline']=round(time.perf_counter()-started,3)
        import torch
        report['torch_version']=torch.__version__
        report['torch_cuda_available']=torch.cuda.is_available()
        black=Path(directory)/'no-face.jpg'
        generated=command(['-y','-f','lavfi','-i','color=c=black:s=640x480','-frames:v','1',str(black)])
        if generated.returncode: raise RuntimeError('Could not generate no-face test frame')
        no_face=perception.face.predict([black])
        report['results']['no_face_check']=no_face.model_dump()
        if no_face.available or no_face.scores: report['errors']['no_face_check']='Unexpected measurement without a face'
    if args.llm:
        from fastapi.testclient import TestClient
        from backend.app.main import app
        with TestClient(app) as client:
            user=client.post('/api/users',json={'name':'Real smoke test'}).json()
            session=client.post('/api/sessions',json={'user_id':user['id']})
            if session.status_code!=201:report['errors']['llm']=session.text
            else:
                with source.open('rb') as file:
                    turn=client.post(f"/api/sessions/{session.json()['id']}/turns",data={'consent':'true'},files={'media':('smoke.webm',file,'video/webm')})
                report['results']['api_turn_status']=turn.status_code
                if turn.status_code==200:
                    report['results']['api_turn']=turn.json()
                    if turn.json()['agent']['reason']=='Provider output did not match the response schema.':
                        report['errors']['structured_response']='Provider response used the explicit formatting fallback'
                else:report['errors']['api_turn']=turn.text
            client.delete(f"/api/users/{user['id']}/history")

output=ROOT/('output/private/real-model-smoke.json' if args.media else 'output/verification/real-model-smoke.json')
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
print(f'Report saved to {output}')
sys.exit(1 if report['errors'] else 0)
