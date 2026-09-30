import json
from pathlib import Path
import tempfile
import unittest
from ragapp.evaluation import evaluate, summarize


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name) / "results.json"
        self.cases = [{"question": "Python?", "source": "p.txt"},
                      {"question": "Hava?", "source": None, "expected_answer": "abstain"}]

    def tearDown(self):
        self.temp.cleanup()

    def answer(self, question):
        return {"question": question, "status": "answered", "total_seconds": 1,
                "retrieved": [{"chunk": {"source": "p.txt"}}]}

    def test_interruption_preserves_progress_and_resume_skips_finished(self):
        def interrupted(q):
            if q == "Hava?":
                raise KeyboardInterrupt()
            return self.answer(q)
        with self.assertRaises(KeyboardInterrupt):
            evaluate(self.cases, {"model": "m"}, self.output, interrupted)
        self.assertEqual(len(json.loads(self.output.read_text())["results"]), 1)
        seen = []
        def resumed(q):
            seen.append(q)
            return self.answer(q)
        run = evaluate(self.cases, {"model": "m"}, self.output, resumed, resume=True)
        self.assertEqual(seen, ["Hava?"])
        self.assertEqual(len(run["results"]), 2)

    def test_changed_experiment_and_accidental_overwrite_are_rejected(self):
        evaluate(self.cases, {"model": "m"}, self.output, self.answer)
        original = self.output.read_bytes()
        for config, cases, resume in [({"model": "m"}, self.cases, False),
                                      ({"model": "other"}, self.cases, True),
                                      ({"model": "m"}, self.cases[:1], True)]:
            with self.assertRaises(ValueError):
                evaluate(cases, config, self.output, self.answer, resume)
            self.assertEqual(self.output.read_bytes(), original)

    def test_failed_first_question_leaves_empty_resumable_run(self):
        def failed(q):
            raise RuntimeError("Model failure")
        with self.assertRaises(RuntimeError):
            evaluate(self.cases, {}, self.output, failed)
        self.assertEqual(json.loads(self.output.read_text())["results"], [])
        run = evaluate(self.cases, {}, self.output, self.answer, True)
        self.assertEqual(summarize(run)["completed_cases"], 2)

    def test_summary_does_not_count_cited_answer_as_abstention(self):
        run = evaluate(self.cases, {}, self.output, self.answer)
        summary = summarize(run)
        self.assertEqual(summary["retrieval_hits"], 1)
        self.assertEqual(summary["out_of_scope_abstentions"], 0)
        self.assertEqual(summary["out_of_scope_cases_evaluated"], 1)
        self.assertEqual(summarize(run["results"])["total_cases"], None)

    def test_finished_resume_does_not_call_model(self):
        evaluate(self.cases, {}, self.output, self.answer)
        def unexpected(q):
            self.fail("Finished run invoked model")
        evaluate(self.cases, {}, self.output, unexpected, True)
