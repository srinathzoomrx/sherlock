# -*- coding: utf-8 -*-
from nltk.corpus import stopwords
import cricket


class token_handler:
    def __init__(self):
        self.schema = cricket.schema
        self.select_nodes = ['select', 'list', 'return', 'get']
        self.operator_nodes = {
            'and': "AND",
            'or': "OR",
            'more': ">",
            'greater': ">",
            'less': "<",
            'after': ">",
            'before': "<",
            'not': "!",
            'equal': "=",
            'between': "BETWEEN",
            'average': "AVG",
            'total': "SUM",
            'maximum': "MAX",
            'most': "MAX",
            'greatest': "MAX",
            'highest': "MAX",
            'minimum': "MIN",
            'least': "MIN",
            'smallest': "MIN",
            'lowest': "MIN",
            'how many': "COUNT",
            'number': "COUNT"
        }

        self.complex_questions = {
            "percent": "PERCENT",
            "percentage": "PERCENT"
        }

        self.periods = ["week", "month", "quarter", "year"]
        self.period_definer = ["last", "this", "next"]
        self.defined_periods = ["yesterday", "today", "tomorrow"]

        self.operands = {
            "AND": {"previous1": None, "next1": None},
            "OR": {"previous1": None, "next1": None},
            "GREATER": {"previous1": None, "next1": None},
            "LESSER": {"previous1": None, "next1": None},
            "EQUAL": {"previous1": None, "next1": None},
            "NOT": {"previous1": False, "next1": None}
        }
        self.quantifier_nodes = ['all']
        self.magic_keys = {'each': "G", 'per': "G"}

    def operation_type(self, operation):
        aggregate_operations = ["AVG", "SUM", "MAX", "MIN", "COUNT"]
        logical_operations = ["AND", "OR"]
        relative_operations = [">", "<", "=", "!", ">=", "<="]

        if operation in relative_operations:
            return "Or"
        if operation in logical_operations:
            return "Ol"
        if operation in aggregate_operations:
            return "Og"

    def is_period_definer(self, word):
        if word in self.period_definer:
            return True
        return False

    def get_token_details(self, word):
        if word in self.select_nodes:
            return "SELECT"
        if word in self.complex_questions:
            return {
                'type': "C",
                'sub_type': "Cp",
                'token': word,
                'question_type': self.complex_questions[word],
                'components': {
                    'data': [],
                    'group_type': "",
                    'relations': [],
                    'attributes': [],
                    'expressions': []
                },
            }
        if word in self.period_definer:
            return {
                'type': "T",
                'sub_type': "Td",
                'token': word,
                'definer': word
            }
        if word in self.periods:
            return {
                'type': "T",
                'sub_type': "Tp",
                'token': word,
                'period': word
            }
        if word in self.defined_periods:
            return {
                'type': "T",
                'sub_type': "Tdp",
                'token': word,
                'period': word
            }
        if word.lower() in self.operator_nodes:
            return {
                'type': "O",
                'sub_type': self.operation_type(self.operator_nodes[word.lower()]),
                'operation': self.operator_nodes[word.lower()],
                'token': word,
                # 'operation_type' : operation_types[operator_nodes[word]]
                'explicit': True
            }
        # In data model (relation, attribute or value)
        if (word.lower() in self.schema):
            if len(self.schema[word.lower()]) == 1:
                return self.schema[word.lower()][0]
            else:
                return self.schema[word.lower()]
                # conflict solution
        if word.isdigit():
            return {
                'type': "I",
                'token': word,
                'number': word
            }
        # filler node management
        if word in set(stopwords.words('english')):
            return None
        # # Multiple assignment conflict management [for now with precedence]
        # Undefined words
        return False
