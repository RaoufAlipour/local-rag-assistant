"""Aynı kaynak seçimi isteğinde 192 ve 64 çıktı sınırını karşılaştırır.

Çevrimdışı, cevap önbelleksiz; uygulama ayarlarını ve indeksi değiştirmez.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ragapp.evaluation import save_json
from ragapp.evidence import evidence_units, scope_definition, scope_event_date, selection_prompt, parse_selection


def compare(runs):
    groups = {cap: [r for r in runs if r['limit'] == cap] for cap in (192, 64)}
    means = {str(cap): round(statistics.mean(r['seconds'] for r in rows), 4)
             for cap, rows in groups.items() if len(rows) == 2 and all(r.get('valid') for r in rows)}
    consistent = len(runs) == 4 and all(r.get('valid') for r in runs) and len({tuple(r.get('selected_ids', [])) for r in runs}) == 1
    baseline = groups[192]
    order_effect = len(baseline) == 2 and min(r['seconds'] for r in baseline) > 0 and max(r['seconds'] for r in baseline) / min(r['seconds'] for r in baseline) > 1.2
    return {'mean_seconds': means, 'all_selections_equal': consistent,
            'possible_order_effect': order_effect,
            'candidate_speedup_ratio': round(means['192']/means['64'], 3) if consistent and not order_effect and set(means) == {'192', '64'} and means['64'] > 0 else None,
            'note': 'Tek soru keşif ölçümüdür. 192 sınırının iki süresi %20’den fazla ayrışırsa sıra/ısınma etkisi olabileceğinden hız oranı verilmez. Doğruluk onayı değildir.'}


class GpuMonitor:
    def __init__(self):
        self.samples = []
        self.stop = threading.Event()
        self.executable = shutil.which('nvidia-smi')
        self.thread = None

    def start(self):
        if self.executable:
            self.thread = threading.Thread(target=self._poll, daemon=True)
            self.thread.start()

    def _poll(self):
        while not self.stop.is_set():
            row = {'at': time.time()}
            try:
                result = subprocess.run([self.executable, '--query-gpu=index,memory.used,memory.total,utilization.gpu,pstate',
                                         '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                row['csv'] = result.stdout.strip()
                row['error'] = result.stderr.strip() if result.returncode else None
            except Exception as exc:
                row['error'] = str(exc)
            self.samples.append(row)
            self.stop.wait(1)

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', default='break ile continue farkı nedir?')
    parser.add_argument('--output', type=Path, default=ROOT/'storage/speed-check.json')
    args = parser.parse_args()
    if not args.question.strip():
        parser.error('Soru boş olamaz.')
    if not (ROOT/'storage/knowledge.db').is_file():
        parser.error('Önce belge indeksini oluşturun.')
    from ragapp.core import Store
    from ragapp.foundry import Runtime, FoundryEmbedder, FoundryGenerator
    runtime = None
    monitor = GpuMonitor()
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'question': args.question,
              'cache_used': False, 'offline': True, 'order': [192, 64, 64, 192], 'runs': [],
              'gpu_csv_columns': ['index', 'memory_used_MiB', 'memory_total_MiB', 'gpu_utilization_percent', 'pstate']}
    try:
        monitor.start()
        start = time.perf_counter()
        runtime = Runtime(offline=True)
        embedder = FoundryEmbedder(runtime, 'qwen3-embedding-0.6b')
        report['setup_seconds'] = round(time.perf_counter()-start, 4)
        with Store(ROOT/'storage/knowledge.db') as store:
            start = time.perf_counter()
            hits = store.retrieve(args.question, embedder, 3, 0.35, mode='hybrid')
            report['retrieval_seconds'] = round(time.perf_counter()-start, 4)
        units = evidence_units(hits)
        units, subject = scope_definition(args.question, units)
        if subject is None:
            units, subject = scope_event_date(args.question, units)
        if not units:
            raise ValueError('Bu soruda model çağrısı gerektiren kaynak bulunmadı; belgede cevabı bulunan başka bir soru seçin.')
        system, user = selection_prompt(args.question, units)
        report.update(prompt={'system': system, 'user': user}, source_sentence_count=len(units), device=runtime.device)
        generator = FoundryGenerator(runtime, 'qwen2.5-7b')
        print('Model hazırlanıyor; ilk yükleme ayrı kaydedilecek.', flush=True)
        warm = generator.generate('Kısa cevap ver.', 'Yalnız TAMAM yaz.', max_output_tokens=8)
        report['warmup'] = {'output': warm, 'timings': dict(generator.last_timings)}
        save_json(args.output, report)
        for i, cap in enumerate(report['order'], 1):
            print(f'[{i}/4] Aynı kaynaklar, çıktı sınırı {cap}…', flush=True)
            start = time.perf_counter()
            row = {'limit': cap, 'started_at_epoch': time.time()}
            try:
                raw = generator.generate(system, user, max_output_tokens=cap)
                row.update(raw_output=raw, timings=dict(generator.last_timings))
                selected = parse_selection(raw, units)
                row.update(valid=True, selected_ids=[v['id'] for v in selected])
            except Exception as exc:
                row.update(valid=False, error=str(exc))
            row['seconds'] = round(time.perf_counter()-start, 4)
            report['runs'].append(row)
            report['comparison'] = compare(report['runs'])
            save_json(args.output, report)
            print(f"  {row['seconds']:.2f} saniye · geçerli seçim: {row['valid']}", flush=True)
        return 0
    except Exception as exc:
        report['error'] = str(exc)
        print('Ölçüm tamamlanamadı: '+str(exc), file=sys.stderr)
        return 1
    finally:
        monitor.close()
        report['gpu_samples'] = monitor.samples
        report['gpu_monitor_available'] = bool(monitor.executable)
        save_json(args.output, report)
        if runtime is not None:
            runtime.close()
        print(json.dumps(report.get('comparison', {}), ensure_ascii=False, indent=2))
        print('Ölçüm kaydı: '+str(args.output))


if __name__ == '__main__':
    raise SystemExit(main())
