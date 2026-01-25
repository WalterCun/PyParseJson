import unittest
import json
from ppj.engine.context import Context
from ppj.engine.stages.repair import RepairStage

class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.stage = RepairStage()

    def _process(self, text):
        context = Context(text)
        self.stage.process(context)
        return context.current_text

    def test_empty_string(self):
        # No debería crashear, aunque no produzca JSON válido
        res = self._process("")
        self.assertEqual(res, "")

    def test_only_separators(self):
        # ,,, :::
        res = self._process(",,, :::")
        # No esperamos milagros, solo no crash
        self.assertIsNotNone(res)

    def test_deeply_nested_unclosed(self):
        text = '{"a": {"b": {"c": 1'
        res = self._process(text)
        # Debería cerrar todas
        self.assertTrue(res.endswith('}}}'))
        json.loads(res) # Debe ser válido

    def test_multiple_roots_attempt(self):
        # JSON estándar no permite múltiples raíces, pero el parser tolerante
        # podría envolverlos en una lista o quedarse con el primero/último?
        # Nuestra regla WrapLoosePairs envuelve en {} si no empieza con {/[
        # Si tenemos {"a":1} {"b":2}, WrapLoosePairs no aplica (empieza con {).
        # AddMissingCommas podría poner coma: {"a":1}, {"b":2}
        # Esto sigue sin ser JSON válido (dos objetos).
        # Por ahora, verificamos que no explote.
        text = '{"a":1} {"b":2}'
        res = self._process(text)
        self.assertIsNotNone(res)
        
    def test_weird_characters(self):
        text = 'key: value\x00' # Null byte
        res = self._process(text)
        # Python json parser puede fallar con null bytes, pero RepairStage
        # no tiene regla explícita para quitarlos.
        # Solo verificamos estabilidad.
        self.assertIn('"key"', res)

    def test_single_values(self):
        # "just text"
        # WrapLoosePairs -> {"just text"} -> inválido (set/object sin valor)
        # Si el input no es par clave-valor, es difícil inferir.
        pass
