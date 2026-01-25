import unittest
import json
from ppj.engine.context import Context
from ppj.rules.syntax.separators import EqualToColonRule
from ppj.rules.syntax.quotes import AddQuotesToKeysRule
from ppj.rules.syntax.commas import RemoveTrailingCommasRule, AddMissingCommasRule
from ppj.rules.syntax.brackets import CloseBracketsRule, WrapLoosePairsRule, TupleToListRule
from ppj.rules.syntax.literals import NormalizeBooleansRule, QuoteUnquotedValuesRule

class TestSyntaxRules(unittest.TestCase):
    """
    Tests unitarios para cada regla sintáctica individual.
    Verifica que cada regla haga su trabajo específico sin depender de otras.
    """

    def _apply_rule(self, rule_class, text):
        context = Context(text)
        rule = rule_class()
        if rule.applies(context):
            rule.apply(context)
        return context.current_text

    def test_equal_to_colon(self):
        # Caso básico
        self.assertEqual(self._apply_rule(EqualToColonRule, "key=value"), "key:value")
        # Con espacios
        self.assertEqual(self._apply_rule(EqualToColonRule, "key  =  value"), "key:value")
        # Múltiples
        self.assertEqual(self._apply_rule(EqualToColonRule, "a=1, b=2"), "a:1, b:2")

    def test_add_quotes_to_keys(self):
        # Caso básico
        self.assertEqual(self._apply_rule(AddQuotesToKeysRule, "key: value"), '"key": value')
        # Ya tiene comillas (no debe cambiar)
        self.assertEqual(self._apply_rule(AddQuotesToKeysRule, '"key": value'), '"key": value')
        # Identificadores con guiones bajos y números
        self.assertEqual(self._apply_rule(AddQuotesToKeysRule, "my_key_1: value"), '"my_key_1": value')

    def test_remove_trailing_commas(self):
        self.assertEqual(self._apply_rule(RemoveTrailingCommasRule, '{"a": 1,}'), '{"a": 1}')
        self.assertEqual(self._apply_rule(RemoveTrailingCommasRule, '[1, 2, ]'), '[1, 2]')
        self.assertEqual(self._apply_rule(RemoveTrailingCommasRule, '{"a": 1, }'), '{"a": 1}')

    def test_add_missing_commas(self):
        # Entre strings
        self.assertEqual(self._apply_rule(AddMissingCommasRule, '"a":1 "b":2'), '"a":1, "b":2')
        # Entre número y clave
        self.assertEqual(self._apply_rule(AddMissingCommasRule, '"a":1 "b":2'), '"a":1, "b":2')
        # Entre boolean y clave
        self.assertEqual(self._apply_rule(AddMissingCommasRule, '"a":true "b":false'), '"a":true, "b":false')

    def test_tuple_to_list(self):
        self.assertEqual(self._apply_rule(TupleToListRule, '(1, 2, 3)'), '[1, 2, 3]')
        self.assertEqual(self._apply_rule(TupleToListRule, '{"a": (1, 2)}'), '{"a": [1, 2]}')

    def test_normalize_booleans(self):
        # Variantes de true
        self.assertIn('true', self._apply_rule(NormalizeBooleansRule, 'key: si').lower())
        self.assertIn('true', self._apply_rule(NormalizeBooleansRule, 'key: True').lower())
        self.assertIn('true', self._apply_rule(NormalizeBooleansRule, 'key: yes').lower())
        # Variantes de false
        self.assertIn('false', self._apply_rule(NormalizeBooleansRule, 'key: no').lower())
        self.assertIn('false', self._apply_rule(NormalizeBooleansRule, 'key: False').lower())
        # Null
        self.assertIn('null', self._apply_rule(NormalizeBooleansRule, 'key: None').lower())

    def test_quote_unquoted_values(self):
        # Fechas
        res = self._apply_rule(QuoteUnquotedValuesRule, '"date": 2022-01-01')
        self.assertIn('"2022-01-01"', res)
        # Strings sin comillas
        res = self._apply_rule(QuoteUnquotedValuesRule, '"status": active')
        self.assertIn('"active"', res)
        # No debe tocar números válidos
        res = self._apply_rule(QuoteUnquotedValuesRule, '"count": 123')
        self.assertIn('123', res)
        # No debe tocar booleanos
        res = self._apply_rule(QuoteUnquotedValuesRule, '"valid": true')
        self.assertIn('true', res)

    def test_close_brackets(self):
        self.assertEqual(self._apply_rule(CloseBracketsRule, '{"a": 1'), '{"a": 1}')
        self.assertEqual(self._apply_rule(CloseBracketsRule, '[1, 2'), '[1, 2]')
        # Anidados
        self.assertEqual(self._apply_rule(CloseBracketsRule, '{"a": [1, 2'), '{"a": [1, 2]}')

    def test_wrap_loose_pairs(self):
        self.assertEqual(self._apply_rule(WrapLoosePairsRule, '"a": 1'), '{"a": 1}')
        # No debe envolver si ya tiene llaves
        self.assertEqual(self._apply_rule(WrapLoosePairsRule, '{"a": 1}'), '{"a": 1}')
