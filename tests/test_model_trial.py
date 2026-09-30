import unittest
from unittest.mock import patch
from types import SimpleNamespace
from scripts.compare_models import candidate_text, TrialGenerator, CANDIDATE, BASELINE

class ModelTrialTests(unittest.TestCase):
    def test_only_empty_thinking_wrapper_removed(self):
        self.assertEqual(candidate_text('<think>\n\n</think>\n{"selections":[]}'),'{"selections":[]}')
        text='<think>Reasoning</think>{"selections":[]}'
        self.assertEqual(candidate_text(text),text)
        self.assertEqual(candidate_text('bad output'),'bad output')

    def test_candidate_control_and_raw_audit_are_scoped(self):
        calls=[]
        fake=SimpleNamespace(last_timings={'total_seconds':1},generate=lambda s,u:calls.append((s,u)) or '<think> </think>{"selections":[]}')
        with patch('ragapp.foundry.FoundryGenerator',return_value=fake):
            trial=TrialGenerator(None,CANDIDATE)
            self.assertEqual(trial.generate('system','user'),'{"selections":[]}')
            self.assertEqual(calls[-1],('system','user\n/no_think'))
            self.assertTrue(trial.last_timings['raw_sdk_output'].startswith('<think>'))
            baseline=TrialGenerator(None,BASELINE)
            self.assertTrue(baseline.generate('system','user').startswith('<think>'))
            self.assertEqual(calls[-1],('system','user'))
