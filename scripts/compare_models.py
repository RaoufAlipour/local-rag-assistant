"""prepare: çevrimiçi aday hazırlığı; run: ayrı süreçlerde çevrimdışı karşılaştırma."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ragapp.evaluation import save_json, digest
BASELINE='qwen2.5-7b'
CANDIDATE='qwen3-4b'
CASES=[
 ('break ile continue farkı nedir?','03-donguler.txt','break en içteki döngüyü bitirir; continue mevcut turu atlar.'),
 ('print ile return aynı şey mi?','04-fonksiyonlar.txt','print ekrana yazar ve None döndürür; return çağırana değer verir.'),
 ('raise ValueError ile return ValueError farkı nedir?','06-hatalar-dosyalar.txt','raise istisna yükseltir; return ValueError sınıfını döndürür.'),
 ('TensorFlow ile görüntü sınıflandırması nasıl eğitilir?',None,'Bu bilgi notlarda yok; ret bekleniyor.'),
 ('Python 4 hangi tarihte yayımlanacak?',None,'Bu bilgi notlarda yok; ret bekleniyor.')]


def candidate_text(text):
    # Yalnız boş düşünme kabuğunu kaldır. Dolu düşünce veya hatalı JSON gizlenmez.
    return re.sub(r'^\s*<think>\s*</think>\s*','',text,count=1)


class TrialGenerator:
    def __init__(self, runtime, alias):
        from ragapp.foundry import FoundryGenerator
        self.inner=FoundryGenerator(runtime,alias)
        self.alias=alias
        self.last_timings={}

    def generate(self,system,user):
        if self.alias == CANDIDATE:
            user += '\n/no_think'
        raw=self.inner.generate(system,user)
        self.last_timings={**self.inner.last_timings,'raw_sdk_output':raw,
                           'no_think_requested':self.alias == CANDIDATE}
        return candidate_text(raw) if self.alias == CANDIDATE else raw


def prepare():
    from ragapp.foundry import Runtime
    from ragapp.local_catalog import validate_snapshot
    path=ROOT/'storage/offline-models.json'
    snapshot=json.loads(path.read_text(encoding='utf-8'))
    old=validate_snapshot(snapshot,'cuda')
    aliases={m['alias'] for m in old}
    if not {BASELINE,'qwen3-embedding-0.6b'} <= aliases:
        raise ValueError('Önce mevcut 7B ve embedding yerel kataloğu hazırlanmalı.')
    runtime=Runtime(device='cuda')
    try:
        # Önce CUDA varyantını doğrula; CPU'ya sessiz geçiş yok.
        model=runtime.model(CANDIDATE)
        print(json.dumps(runtime.describe(model),ensure_ascii=False,indent=2),flush=True)
        runtime.prepare([CANDIDATE])
        models=[m for m in old if m['alias'] != CANDIDATE]+[asdict(runtime.model(CANDIDATE).info)]
        updated={**snapshot,'models':models,'digest':digest(models)}
        validate_snapshot(updated,'cuda')
        save_json(path,updated)
        print('Aday hazır. 7B modeli ve eski katalog kayıtları korundu. İndeksleme gerekmez.')
    finally:
        runtime.close()


def worker(alias,output):
    from ragapp.foundry import Runtime,FoundryEmbedder
    from ragapp.core import Store,answer
    from scripts.check_speed import GpuMonitor
    runtime=None; monitor=GpuMonitor()
    report={'model':alias,'offline':True,'answer_mode':'extractive','results':[],
            'cache_used':False,'no_think_requested':alias==CANDIDATE}
    try:
        monitor.start()
        runtime=Runtime(offline=True)
        if runtime.device!='cuda':
            raise ValueError('Karşılaştırma CUDA içindir.')
        embedder=FoundryEmbedder(runtime,'qwen3-embedding-0.6b')
        generator=TrialGenerator(runtime,alias)
        report['model_metadata']=runtime.describe(runtime.model(alias))
        with Store(ROOT/'storage/knowledge.db') as store:
            report['index_digest']=digest(store.db.execute('SELECT source,page,position,content,embedding FROM chunks ORDER BY source,page,position').fetchall())
            print(alias+': tam kaynak isteğiyle hazırlanıyor…',flush=True)
            report['warmup']=answer(CASES[0][0],store,embedder,generator,answer_mode='extractive')
            save_json(output,report)
            for i,(question,source,expected) in enumerate(CASES,1):
                print(f'{alias} [{i}/{len(CASES)}] {question}',flush=True)
                result=answer(question,store,embedder,generator,answer_mode='extractive')
                report['results'].append({'expected_source':source,'expected_answer':expected,'result':result})
                save_json(output,report)
                print(f"  {result['status']} · {result['total_seconds']:.2f} saniye",flush=True)
    finally:
        monitor.close()
        report['gpu_samples']=monitor.samples
        report['gpu_csv_columns']=['index','memory_used_MiB','memory_total_MiB','gpu_utilization_percent','pstate']
        report['quality_note']='Kaynak etiketi veya aynı cevap tek başına doğruluk onayı değildir. Beklenen açıklamayla insan incelemesi gerekir.'
        save_json(output,report)
        if runtime is not None:
            runtime.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run','worker'])
    parser.add_argument('--model',choices=[BASELINE,CANDIDATE])
    parser.add_argument('--output',type=Path,default=ROOT/'storage/models-comparison.json')
    args=parser.parse_args()
    try:
        if args.action=='prepare':
            prepare()
        elif args.action=='worker':
            if args.model is None:parser.error('worker için --model gerekli')
            worker(args.model,args.output)
        else:
            output=args.output.resolve()
            bundle={'runs':[],'complete':False,'warmup_excluded_from_results':True}
            save_json(output,bundle)
            for alias in (BASELINE,CANDIDATE):
                dest=output.with_name(output.stem+'-'+alias+'.json')
                dest.unlink(missing_ok=True)  # Eski koşum sonucu yeni ölçüm sanılmasın.
                # Process exit releases native allocations before the next model starts.
                proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'worker','--model',alias,'--output',str(dest)],cwd=ROOT)
                if dest.is_file():bundle['runs'].append(json.loads(dest.read_text(encoding='utf-8')))
                save_json(output,bundle)
                if proc.returncode:
                    raise RuntimeError(alias+' ölçümü tamamlanamadı. Kısmi kayıt: '+str(output))
            bundle['complete']=True
            if len({r['index_digest'] for r in bundle['runs']})!=1:
                bundle['complete']=False
                bundle['warning']='İndeks iki koşum arasında değişmiş; doğrudan kıyaslamayın.'
            save_json(output,bundle)
            print('Karşılaştırma kaydı: '+str(output))
        return 0
    except Exception as exc:
        print('Hata: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
