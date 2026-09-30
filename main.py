"""Kullanım: python main.py --help"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from ragapp.core import Store, answer

ROOT = Path(__file__).resolve().parent


def doctor():
    packages = {}
    for name in ("foundry-local-sdk", "pypdf"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "kurulu değil"
    print(json.dumps({"python": platform.python_version(), "os": platform.platform(),
                      "architecture": platform.machine(), "packages": packages,
                      "python_supported": (3, 11) <= sys.version_info[:2] < (3, 15)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Yerel Python ders asistanı")
    parser.add_argument("command", choices=["doctor", "models", "prepare", "snapshot", "hello", "ingest", "search", "ask", "chat", "evaluate", "report"])
    parser.add_argument("question", nargs="?")
    parser.add_argument("--documents", type=Path, default=ROOT / "data/documents")
    parser.add_argument("--db", type=Path, default=ROOT / "storage/knowledge.db")
    parser.add_argument("--embedding-model", default="qwen3-embedding-0.6b")
    parser.add_argument("--chat-model", help="Açıkça seçilen sohbet modeli; kalite onaylı varsayılan henüz yok")
    parser.add_argument("--device", choices=["cpu", "cuda"],
                        help="Cihaz; belirtilmezse prepare ile kaydedilen ayar, yoksa cpu")
    parser.add_argument("--offline", action="store_true", help="snapshot ile kaydedilmiş yerel katalog kullan")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--retrieval-mode", choices=["hybrid", "semantic"], default="hybrid",
                        help="hybrid: cosine + BM25; semantic: yalnız cosine eşiği")
    parser.add_argument("--answer-mode", choices=["generative", "extractive"], default="generative",
                        help="generative: model açıklaması; extractive: seçilen kaynak cümlelerini aynen göster")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--overlap", type=int, default=30)
    parser.add_argument("--cases", type=Path, default=ROOT / "data/evaluation.json")
    parser.add_argument("--limit", type=int, help="evaluate: ilk N soruyla kısa ölçüm; tam kalite testi değildir")
    parser.add_argument("--output", type=Path, default=ROOT / "storage/evaluation-results.json")
    parser.add_argument("--resume", action="store_true", help="Aynı değerlendirmeye kaldığı yerden devam et")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and (args.command != "evaluate" or args.limit < 1):
        parser.error("--limit yalnız evaluate için pozitif bir sayı olabilir.")
    if args.command == "doctor":
        doctor()
        return 0
    if args.command in {"prepare", "snapshot", "hello", "ask", "chat", "evaluate"} and not args.chat_model:
        parser.error("--chat-model belirtin. Model kalite sonuçları için docs/QUALITY-NOTES.md dosyasını okuyun.")
    if args.offline and args.command in {"prepare", "snapshot"}:
        parser.error("prepare ve snapshot --offline ile kullanılamaz.")
    if args.command in {"ask", "search"} and (not args.question or not args.question.strip()):
        parser.error("Bu komut için bir soru yazın.")
    if args.command in {"search", "ask", "chat", "evaluate"} and not args.db.is_file():
        parser.error("Veritabanı bulunamadı; önce ingest çalıştırın.")
    if args.command == "report":
        from ragapp.evaluation import summarize
        try:
            print(json.dumps(summarize(json.loads(args.output.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2))
            return 0
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f"Rapor okunamadı: {exc}")
    runtime = None
    try:
        from ragapp.foundry import Runtime, FoundryEmbedder, FoundryGenerator
        runtime = Runtime(device=args.device, offline=args.offline)
        if args.command == "models":
            aliases = [args.embedding_model, args.chat_model] if args.chat_model else None
            print(json.dumps(runtime.models(aliases), ensure_ascii=False, indent=2))
            return 0
        if args.command == "prepare":
            runtime.prepare([args.embedding_model, args.chat_model])
            return 0
        if args.command == "snapshot":
            runtime.snapshot([args.embedding_model, args.chat_model])
            return 0
        generator = FoundryGenerator(runtime, args.chat_model)
        if args.command == "hello":
            print(generator.generate("Answer briefly.", "Say hello in Turkish."))
            return 0
        embedder = FoundryEmbedder(runtime, args.embedding_model)
        with Store(args.db) as store:
            if args.command == "ingest":
                print(json.dumps(store.ingest(args.documents, embedder, args.chunk_size, args.overlap), indent=2))
            elif args.command == "search":
                from dataclasses import asdict
                hits = store.retrieve(args.question, embedder, args.top_k, args.threshold, mode=args.retrieval_mode)
                print(json.dumps([asdict(h) for h in hits], ensure_ascii=False, indent=2))
            elif args.command == "evaluate":
                from ragapp.evaluation import evaluate, digest, summarize
                cases = json.loads(args.cases.read_text(encoding="utf-8"))
                if args.limit is not None:
                    cases = cases[:args.limit]
                configuration = {
                    "embedding_identity": embedder.identity,
                    "device": runtime.device,
                    "catalog_mode": "local_snapshot" if args.offline else "default",
                    "chat_model": args.chat_model,
                    "chat_model_id": runtime.model(args.chat_model).id,
                    "chat_model_metadata": runtime.describe(runtime.model(args.chat_model)),
                    "embedding_model_metadata": runtime.describe(embedder.model),
                    "top_k": args.top_k, "threshold": args.threshold,
                    "retrieval_mode": args.retrieval_mode,
                    "answer_mode": args.answer_mode,
                    "index_digest": digest(store.db.execute(
                        "SELECT source,page,position,content,embedding FROM chunks ORDER BY source,page,position").fetchall()),
                    "code_digest": digest({name: (ROOT / name).read_text(encoding="utf-8") for name in
                                           ("ragapp/core.py", "ragapp/evidence.py", "ragapp/retrieval.py", "ragapp/foundry.py", "ragapp/local_catalog.py", "ragapp/evaluation.py", "main.py")}),
                    "platform": platform.platform(),
                }
                run = evaluate(cases, configuration, args.output,
                               lambda q: answer(q, store, embedder, generator, args.top_k, args.threshold, args.retrieval_mode, args.answer_mode), args.resume)
                print(json.dumps(summarize(run), ensure_ascii=False, indent=2))
                print(f"Değerlendirme kaydı: {args.output}")
            else:
                def display(q):
                    result = answer(q, store, embedder, generator, args.top_k, args.threshold, args.retrieval_mode, args.answer_mode)
                    if args.json:
                        print(json.dumps(result, ensure_ascii=False, indent=2))
                    else:
                        if result["answer_mode"] == "extractive" and result["status"] == "answered":
                            print("\nKaynaklardan seçilen cümleler:")
                        print("\n" + result["answer"])
                        for i in result["citations"]:
                            h = result["retrieved"][i-1]
                            c = h["chunk"]
                            print(f"[S{i}] {c['source']} | sayfa {c['page']} | benzerlik {h['score']:.3f}")
                        if result["status"] in {"invalid_citations", "conflicting_answer", "invalid_evidence"}:
                            for h in result["retrieved"]:
                                print(f"[{h['id']}] {h['chunk']['source']}: {h['chunk']['content']}")
                        print(f"Süre: {result['total_seconds']:.2f} saniye")
                if args.command == "ask":
                    display(args.question)
                else:
                    print("Python Notları Asistanı | Çıkış: /exit | Her soru bağımsız değerlendirilir.")
                    while True:
                        try:
                            q = input("\nSorunuz: ").strip()
                        except EOFError:
                            break
                        if q == "/exit":
                            break
                        if q:
                            display(q)
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        print(f"Hata: {exc or 'İşlem durduruldu.'}", file=sys.stderr)
        print("Kurulumu kontrol etmek için: python main.py doctor", file=sys.stderr)
        return 1
    finally:
        if runtime is not None:
            try:
                runtime.close()
            except Exception as exc:
                print(f"Modeli kapatırken hata: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
