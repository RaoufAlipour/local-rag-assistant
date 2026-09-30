import unittest
from scripts.check_speed import compare
from ragapp.foundry import FoundryGenerator

class SpeedCheckTests(unittest.TestCase):
    def test_different_or_invalid_selection_cannot_claim_speedup(self):
        rows=[dict(limit=c,seconds=2,valid=True,selected_ids=['S1.1']) for c in [192,64,64,192]]
        self.assertEqual(compare(rows)['candidate_speedup_ratio'],1)
        rows[1]['selected_ids']=[]
        self.assertIsNone(compare(rows)['candidate_speedup_ratio'])
        rows[1]['valid']=False
        self.assertNotIn('64',compare(rows)['mean_seconds'])

    def test_partial_run_has_no_speedup(self):
        self.assertIsNone(compare([dict(limit=192,seconds=1,valid=True,selected_ids=[])])['candidate_speedup_ratio'])

    def test_invalid_budget_rejected_before_model_load(self):
        generator=FoundryGenerator(None,'unused')
        for value in (0,True,1.5,4097):
            with self.assertRaises(ValueError):
                generator.generate('','',max_output_tokens=value)

    def test_budget_forwarded_and_whitespace_measured_without_changing_response(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        options=[]
        fake=SimpleNamespace(ChatSession=MagicMock(),Request=MagicMock(),
            RequestOptions=lambda **kw: kw,
            SearchOptions=lambda **kw: options.append(kw) or kw,
            MessageItem=SimpleNamespace(system=lambda x:x,user=lambda x:x),TextItem=object)
        runtime=SimpleNamespace(load=lambda alias: object(),last_load_timings={})
        with patch.dict(sys.modules,{'foundry_local_sdk':fake}), patch('ragapp.foundry.response_text',return_value='{}   '):
            generator=FoundryGenerator(runtime,'test')
            self.assertEqual(generator.generate('sys','user',max_output_tokens=64),'{}   ')
        self.assertEqual(options[0]['max_output_tokens'],64)
        self.assertEqual(generator.last_timings['trailing_whitespace_characters'],3)
        self.assertEqual(generator.last_timings['prompt_characters'],7)

    def test_cold_first_full_prompt_does_not_claim_token_budget_speedup(self):
        rows=[dict(limit=c,seconds=t,valid=True,selected_ids=['S1.9','S1.10'])
              for c,t in [(192,25.1439),(64,13.5613),(64,13.5146),(192,13.5534)]]
        report=compare(rows)
        self.assertTrue(report['possible_order_effect'])
        self.assertIsNone(report['candidate_speedup_ratio'])

    def test_vram_comparison_excludes_warmup_and_requires_valid_equal_selections(self):
        from scripts.check_vram import summarize
        rows=[dict(phase=p,seconds=t,valid=True,selected_ids=['S1.1']) for p,t in
              [('full_prompt_warmup',99),('both_loaded',13),('embedding_unloaded',4),('embedding_unloaded',3)]]
        self.assertEqual(summarize(rows)['both_loaded_seconds'],13)
        self.assertTrue(summarize(rows)['comparable'])
        rows[-1]['selected_ids']=[]
        self.assertFalse(summarize(rows)['comparable'])
        rows[-1]['valid']=False
        self.assertFalse(summarize(rows)['comparable'])
