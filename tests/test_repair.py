import unittest
from ppj.engine.context import Context
from ppj.engine.stages.repair import RepairStage

class TestRepairStage(unittest.TestCase):
    def setUp(self):
        self.stage = RepairStage()

    def test_basic_repair(self):
        text = 'banco=si , cooperative: no, vauche:1231235'
        context = Context(text)
        self.stage.process(context)
        
        self.assertIn('"banco":true', context.current_text)
        self.assertIn('"cooperative":false', context.current_text)
        self.assertTrue(context.current_text.startswith('{'))
        self.assertTrue(context.current_text.endswith('}'))

    def test_missing_quotes_and_brackets(self):
        text = '{bank:0 cooperative:0 voucher:1 deposit_date:01-01-2026}'
        context = Context(text)
        self.stage.process(context)
        
        self.assertIn('"bank":0', context.current_text)
        self.assertIn(',', context.current_text)
        # Ahora con QuoteUnquotedValuesRule, esto debería funcionar
        self.assertIn('"deposit_date":"01-01-2026"', context.current_text)

    def test_tuple_to_list(self):
        text = '(1, 2, 3)'
        context = Context(text)
        self.stage.process(context)
        self.assertEqual(context.current_text, '[1, 2, 3]')

    def test_trailing_comma(self):
        text = '{"a": 1,}'
        context = Context(text)
        self.stage.process(context)
        self.assertEqual(context.current_text, '{"a": 1}')

    def test_close_brackets(self):
        text = '{"a": 1'
        context = Context(text)
        self.stage.process(context)
        self.assertEqual(context.current_text, '{"a": 1}')

if __name__ == '__main__':
    unittest.main()
