# tests/test_tokenizer.py
import pytest
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.core.token import TokenType


def test_simple_pair():
    tokenizer = TolerantTokenizer()
    tokens = tokenizer.tokenize('user: "admin"')

    assert len(tokens) == 3
    assert tokens[0].type == TokenType.BARE_WORD
    assert tokens[0].value == "user"
    assert tokens[1].type == TokenType.COLON
    assert tokens[2].type == TokenType.STRING
    assert tokens[2].value == '"admin"'


def test_boolean_normalization():
    tokenizer = TolerantTokenizer()
    tokens = tokenizer.tokenize('active: si')

    assert tokens[2].type == TokenType.BOOLEAN
    assert tokens[2].value.lower() in ['si', 'true', 'yes']