"""Sohbet modelinden önce embedding modelini kaldırmanın etkisini ölçer.

Tüm çağrılarda aynı istem ve 192 token sınırı kullanılır. İndeks veya ayarlar değişmez.
"""
import argparse
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_speed import GpuMonitor
from ragapp.evaluation import save_json
from ragapp.evidence import evidence_units, selection_prompt, scope_definition, scope_event_date, parse_selection


def summarize(runs):
    baseline = [r for r in runs if r['phase'] == 'both_loaded']
    candidate = [r for r in runs if r['phase'] == 'embedding_unloaded']
    if len(baseline) != 1 or len(candidate) != 2 or not all(r.get('valid') for r in baseline + candidate):
        return {'comparable': False, 'reason': 'Eksik koşum veya geçersiz seçim.'}
    same = len({tuple(r['selected_ids']) for r in baseline + candidate}) == 1
    return {'comparable': same, 'same_selections': same,
            'both_loaded_seconds': baseline[0]['seconds'],
            'embedding_unloaded_seconds': [r['seconds'] for r in candidate],
            'note': 'İlk tam istem hazırlama çağrısı dışlandı. Sabit sıra ve az tekrar nedeniyle genel hız garantisi değildir. Yeniden embedding yükleme maliyeti ölçülmez.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', default='break ile continue farkı nedir?')
    parser.add_argument('--output', type=Path, default=ROOT/'storage/vram-check.json')
    args = parser.parse_args()
    if not args.question.strip() or not (ROOT/'storage/knowledge.db').is_file():
        parser.error('Boş olmayan soru ve mevcut belge indeksi gerekir.')
    from ragapp.core import Store
    from ragapp.foundry import Runtime, FoundryEmbedder, FoundryGenerator
    runtime = None
    monitor = GpuMonitor()
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'question': args.question,
              'offline': True, 'cache_used': False, 'runs': [], 'max_output_tokens': 192,
              'gpu_csv_columns': ['index','memory_used_MiB','memory_total_MiB','gpu_utilization_percent','pstate']}
    try:
        monitor.start()
        runtime = Runtime(offline=True)
        if runtime.device != 'cuda':
            raise ValueError('Bu ölçüm CUDA cihazı içindir; kayıtlı cihaz ayarı CUDA değil.')
        embedder = FoundryEmbedder(runtime, 'qwen3-embedding-0.6b')
        with Store(ROOT/'storage/knowledge.db') as store:
            hits = store.retrieve(args.question, embedder, 3, 0.35, mode='hybrid')
        units, subject = scope_definition(args.question, evidence_units(hits))
        if subject is None:
            units, subject = scope_event_date(args.question, units)
        if not units:
            raise ValueError('Bu soruda model çağrısı için kaynak yok.')
        system, user = selection_prompt(args.question, units)
        report['prompt'] = {'system': system, 'user': user}
        generator = FoundryGenerator(runtime, 'qwen2.5-7b')
        phases = ['full_prompt_warmup', 'both_loaded', 'embedding_unloaded', 'embedding_unloaded']
        for index, phase in enumerate(phases, 1):
            if index == 3:
                print('Embedding modeli kaldırılıyor; aynı kaynaklar bellekte korunuyor.', flush=True)
                start = time.perf_counter()
                embedder.model.unload()
                report['unload_seconds'] = round(time.perf_counter()-start, 4)
                if embedder.model.is_loaded:
                    raise RuntimeError('SDK embedding modelini hâlâ yüklü gösteriyor; karşılaştırma durduruldu.')
                runtime.loaded = [m for m in runtime.loaded if m is not embedder.model]
            print(f'[{index}/4] {phase}', flush=True)
            start = time.perf_counter()
            row = {'phase': phase, 'started_at_epoch': time.time()}
            try:
                raw = generator.generate(system, user)
                row.update(raw_output=raw, timings=dict(generator.last_timings))
                row.update(valid=True, selected_ids=[v['id'] for v in parse_selection(raw, units)])
            except Exception as exc:
                row.update(valid=False, error=str(exc))
            row['seconds'] = round(time.perf_counter()-start, 4)
            report['runs'].append(row)
            save_json(args.output, report)
            print(f"  {row['seconds']:.2f} saniye · geçerli seçim: {row['valid']}", flush=True)
        return 0
    except Exception as exc:
        report['error'] = str(exc)
        print('Ölçüm tamamlanamadı: '+str(exc), file=sys.stderr)
        return 1
    finally:
        monitor.close()
        report['comparison'] = summarize(report['runs'])
        report['gpu_samples'] = monitor.samples
        report['gpu_monitor_available'] = bool(monitor.executable)
        save_json(args.output, report)
        if runtime is not None:
            runtime.close()
        print(json.dumps(report['comparison'], ensure_ascii=False, indent=2))
        print('Ölçüm kaydı: '+str(args.output))


if __name__ == '__main__':
    raise SystemExit(main())
