import nltk.tree
import re


class semantic_group:
    def __init__(self):
        self.merger_op = {
            'AND': {'OR': False},
            '!': {'=': '!=', '!=': '=', '>': '<=', '<': '>='},
            '=': {'=': '=', '>': '>=', '<': '<='},
            '>': {'OR': '>', '=': '>='},
            '<': {'OR': '<', '=': '<='},
        }

    def create(self, parse_tree):
        """
        Make group of groups from trees
        Arguement - tree - parse_tree

        Return list
        """
        group = []
        for subtree in parse_tree:
            if type(subtree) == nltk.tree.Tree:
                group.append(self.create(subtree))
            else:
                group.append(subtree)

        if len(group) == 1:
            return group[0]
        return group

    def group_type(self, group_structure):
        """ Get type of the group for making proper merging algorithm

        Arguments:
        group_structure - string specifying the structure of the group
        """
        group_types = {
            "R?Ax?R?": "Attribute",
            "I+(Ol)?I": "Integer group",
            "V+(Ol)?V": "Value group",
            "R?(Ag?)+(Ol)?Ag?R?": "Attribute group",
            "(AV+)|(V+(Or)?A)": "Condition",  # av, va, avvo,
            "AI": "Integer condition",
            "Or(V|((I|A)x?))": "Semi-processed Op",
            "Oq((Ol)?Oq)+": "Semi-processed Op group",
            "Ag?Oq": "Process semi-processed Op",
            "Ag?Oqx": "Process semi-processed Op group",
            "(EV)|(VE)|(Ag?[VE])": "Simple group",
            "(OgR?A)|(AOg)": "Aggregate attribute",
            "OgOg": "Aggregate over aggregation",
            "OgR": "Aggregate table",
            "OgE": "Aggregate exp",
            "OgV+": "Aggregate with value",
            "Ogx(R|A|V|E)+": "Complex aggregation question",
            "(A|R)Cg": "Question from complex aggregation",
            "E*OlE": "Expression operation",
            "(AE)|(EA)": "Attribute with Expression",
            "A?OrE": "Operation updation",
            "[EAR]+?E": "Simple group",
            "(V+R)|(RV+)": "Related Conditions",
            "TdTp": "Defined Period",
            "ATdp": "Time Conditions",
            "Cp(E|R|A|V)": "Complex Question"
        }
        for template, group_type in group_types.iteritems():
            pattern = re.compile("\A" + template + "\Z")
            match = pattern.match(group_structure)
            if match:
                return group_type
        print "CHART THIS: <<<<" + group_structure + ">>>>"
        return False

    def merged_data(self, pre_merge_data):
        """
        Merge components to one
        Arguement - data - components of group with other data


        Return - merged component as expression / complex attributes / integer
        """
        # Merge components based on its type
        if pre_merge_data['group_type'] == "Complex Question":
            for token_data in pre_merge_data['data']:
                if token_data['type'] == "C":
                    merged_data = token_data
                    continue
                merged_data['components']['data'].append(token_data)
                merged_data['components']['group_type'] += token_data['type']
                if token_data['type'] == 'R':
                    merged_data['components']['relations'].append(token_data)
                if token_data['type'] == 'A':
                    merged_data['components']['attributes'].append(token_data)
                if token_data['type'] == 'E':
                    merged_data['components']['expressions'].append(token_data)
            return merged_data

        if pre_merge_data['group_type'] == "Attribute":
            if len(pre_merge_data['relations']) > 1:
                # "Expected attribute with one relation"
                return None
            if pre_merge_data['attributes'][0]['relation'] != pre_merge_data['relations'][0]['relation']:
                data = {
                    'type': "E",
                    'conditions': [],
                    'table': [pre_merge_data['relations'][0]['relation'], pre_merge_data['attributes'][0]['relation']],
                    'used_attributes': [pre_merge_data['attributes'][0]],
                    'attributes': []
                }
                return data
            return pre_merge_data['attributes'][0]

        if pre_merge_data['group_type'] == "Integer group":
            data = {
                'type': "I",
                'sub_type': "Ix",
                'numbers': pre_merge_data['data']  # array of token data
            }
            # TODO if operation add operation also
            return data

        if pre_merge_data['group_type'] == "Value group":
            conditions = []
            tables = []
            for value_data in pre_merge_data['data']:
                if value_data['type'] != "V":
                    continue
                conditions.append(self.condition_from_value(value_data, {'operation': "="}))
                if value_data['relation'] not in tables:
                    tables.append(value_data['relation'])
            data = {
                'type': "E",
                'conditions': conditions,
                'table': tables,
                'used_attributes': [{'relation': value_data['relation'], 'attribute': value_data['attribute']}],
                'attributes': []
            }
            return data
        if pre_merge_data['group_type'] == "Attribute group":
            attributes = []
            tables = []
            for attribute_data in pre_merge_data['data']:
                if attribute_data['type'] != "A":
                    continue
                attributes.append(attribute_data)
                if attribute_data['relation'] not in tables:
                    tables.append(attribute_data['relation'])
            data = {'type': "A", 'sub_type': "Ax", 'attributes': attributes, 'table': tables}
            return data

        if pre_merge_data['group_type'] == "Integer condition":  # ai
            attribute = pre_merge_data['attributes'][0]
            used_attributes = [{'relation': attribute['relation'], 'attribute': attribute['attribute']}]
            tables = [attribute['relation']]
            display = 0
            condition = {
                'operation': "=",
                'explicit': True
            }
            for value_data in pre_merge_data['data']:
                if value_data['type'] == "I":
                    condition['RHS'] = value_data
                else:
                    condition['LHS'] = value_data
            data = {
                'type': "E",
                'conditions': [condition],
                'used_attributes': used_attributes,
                'attributes': [],
                'table': tables
            }
            return data

        if pre_merge_data['group_type'] == "Condition":  # av, va, avvov
            conditions = []
            attribute = pre_merge_data['attributes'][0]
            used_attributes = [{'relation': attribute['relation'], 'attribute': attribute['attribute']}]
            tables = [attribute['relation']]
            display = 0
            for value_data in pre_merge_data['data']:
                if value_data['type'] != "V":
                    continue
                if (display != 1 and
                        (value_data['relation'] != attribute['relation'] or
                            value_data['attribute'] != attribute['attribute'])):
                    display = 1
                    new_attr = {'relation': value_data['relation'], 'attribute': value_data['attribute']}
                    if new_attr not in used_attributes:
                        used_attributes.append(new_attr)
                    if value_data['relation'] not in tables:
                        tables.append(value_data['relation'])
                conditions.append(self.condition_from_value(value_data, {'operation': "="}))
            data = {
                'type': "E",
                'conditions': conditions,  # TODO expressions from values
                'used_attributes': used_attributes,
                'attributes': [],
                'table': tables
            }
            if display == 1:
                data['attributes'].append(attribute)
            return data
        if pre_merge_data['group_type'] == "Related Conditions":
            conditions = []
            used_attributes = []
            relation = pre_merge_data['relations'][0]
            tables = [relation['relation']]
            display = 0
            for token_data in pre_merge_data['data']:
                if token_data['type'] != "V":
                    continue
                value_data = token_data
                if value_data['attribute'] not in used_attributes:
                    used_attributes.append(value_data['attribute'])
                if value_data['relation'] != relation['relation']:
                    tables.append(value_data['relation'])
                conditions.append(self.condition_from_value(value_data, {'operation': "="}))
            data = {
                'type': "E",
                'conditions': conditions,  # TODO expressions from values
                'used_attributes': [{'relation': value_data['relation'], 'attribute': value_data['attribute']}],
                'table': tables,
                'attributes': []
            }
            return data
        if pre_merge_data['group_type'] == "Semi-processed Op":
            for operand_data in pre_merge_data['data']:
                if operand_data['type'] != "O":
                    operand = operand_data
            data = {
                'type': "O",
                'sub_type': "Oq",
                'operation': pre_merge_data['operations'][0]['operation'],
                'RHS': operand
            }
            if 'used_attributes' in operand:
                data['used_attributes'] = operand['used_attributes']
            elif 'relation' in operand and 'attribute' in operand:
                data['used_attributes'] = {'relation': operand['relation'], 'attribute': operand['attribute']}
            # operation form RHS operands here, mark used attributes if needed
            return data

        if pre_merge_data['group_type'] == "Semi-processed Op group":
            data = {
                'type': "O",
                'sub_type': "Oqx",
                'operations': [],
            }
            for operation_data in pre_merge_data['data']:
                if operation_data['sub_type'] == "Oq":
                    data['operations'].append(operation_data)
            return data

        if pre_merge_data['group_type'] == "Process semi-processed Op":  # "Ag?Oq"
            condition = pre_merge_data['operations'][0]
            condition['LHS'] = pre_merge_data['attributes']
            used_attributes = []
            tables = []
            if 'used_attributes' in condition:
                used_attributes = condition['used_attributes']
            if 'table' in condition:
                tables = condition['table']
            for attribute in pre_merge_data['attributes']:
                new_attr = {'relation': attribute['relation'], 'attribute': attribute['attribute']}
                if new_attr not in used_attributes:
                    used_attributes.append(new_attr)
                if attribute['relation'] not in tables:
                    tables.append(attribute['relation'])
            data = {
                'type': "E",
                'conditions': [condition],  # TODO expressions from values
                'used_attributes': used_attributes,
                'attributes': [],
                'table': tables
            }
            # create a condition from operation and the attribute - update used attribute also
            return data

        if pre_merge_data['group_type'] == "Process semi-processed Op group":  # "Ag?Oq"
            conditions = pre_merge_data['operations'][0]['operations']
            used_attributes = []
            tables = []
            for x in xrange(0, len(conditions)):
                condition = conditions[x]
                condition['LHS'] = pre_merge_data['attributes']
                if 'used_attributes' in condition:
                    used_attributes.extend(condition['used_attributes'])
                if 'table' in condition:
                    tables.extend(condition['table'])
            for attribute in pre_merge_data['attributes']:
                new_attr = {'relation': attribute['relation'], 'attribute': attribute['attribute']}
                if new_attr not in used_attributes:
                    used_attributes.append(new_attr)
                if attribute['relation'] not in tables:
                    tables.append(attribute['relation'])
            data = {
                'type': "E",
                'conditions': conditions,  # TODO expressions from values
                'used_attributes': used_attributes,
                'attributes': [],
                'table': tables
            }
            # create a condition from operation and the attribute - update used attribute also
            return data

        if pre_merge_data['group_type'] == "Aggregate attribute":
            attribute = pre_merge_data['attributes'][0]
            agg_operation = pre_merge_data['operations'][0]
            if agg_operation['operation'] == "COUNT":
                agg_attr = {
                    'type': "A", 'sub_type': "Ag", 'operation': agg_operation,
                    'relation': attribute['relation'], 'attribute': "*"
                }
                data = {
                    'type': "E", 'attributes': [attribute, agg_attr],
                    'conditions': [], 'table': [attribute['relation']], 'used_attributes': []
                }
                return data
            # if pre_merge_data['operations'][0]['operation'] in ['MAX', 'MIN'] and attribute:

            data = {
                'type': "A", 'sub_type': "Ag", 'operation': pre_merge_data['operations'][0],
                'relation': attribute['relation'], 'attribute': attribute['attribute']
            }
            # form attribute with aggregation operation
            return data

        if pre_merge_data['group_type'] == "Aggregate over aggregation":
            return {
                'type': "O",
                'sub_type': "Ogx",
                'operations': pre_merge_data['data']
            }

        if pre_merge_data['group_type'] == "Aggregate table":
            relation = pre_merge_data['relations'][0]
            agg_operation = pre_merge_data['operations'][0]
            if agg_operation['operation'] != "COUNT":
                raise NotImplementedError('Aggregation on relation is not count')
            agg_attr = {
                'type': "A", 'sub_type': "Ag", 'operation': agg_operation,
                'relation': relation['relation'], 'attribute': "*"
            }
            data = {
                'type': "E", 'attributes': [agg_attr],
                'conditions': [], 'table': [relation['relation']], 'used_attributes': []}

            # form attribute with aggreagation operation and relation [COUNT (*)]
            return data

        if pre_merge_data['group_type'] == "Aggregate exp":
            agg_operation = pre_merge_data['operations'][0]
            if agg_operation['operation'] != "COUNT":
                return False
            data = pre_merge_data['expressions'][0]
            agg_attr = {
                'type': "A", 'sub_type': "Ag", 'operation': agg_operation,
                'relation': data['table'][-1], 'attribute': "*"
            }
            data['attributes'].append(agg_attr)
            # form attribute with aggreagation operation and relation [COUNT (*)]
            return data
        if pre_merge_data['group_type'] == "Aggregate with value":
            agg_operation = pre_merge_data['operations'][0]
            conditions = []
            tables = []
            if agg_operation['operation'] != "COUNT":
                return False
            for token_data in pre_merge_data['data']:
                if token_data['type'] != "V":
                    continue
                conditions.append(self.condition_from_value(token_data, {'operation': "="}))
                if token_data['relation'] not in tables:
                    tables.append(token_data['relation'])
            relation = ""
            if len(tables) == 1:
                relation = tables[0]
            agg_attr = {
                'type': "A", 'sub_type': "Ag", 'operation': agg_operation,
                'relation': relation, 'attribute': "*"
            }
            data = {
                'type': "E", 'attributes': [agg_attr],
                'conditions': conditions, 'table': tables, 'used_attributes': []}
            return data
        if pre_merge_data['group_type'] == "Complex aggregation question":
            operation = pre_merge_data['operations'][0]['operations'][0]
            table = []
            if pre_merge_data['data'][1]['type'] == "R":
                table.append(pre_merge_data['data'][1])
            elif pre_merge_data['data'][1]['type'] == "E":
                table = pre_merge_data['data'][1]['table']
            component_data = [pre_merge_data['operations'][0]['operations'][1]]
            group_type = "Og"
            for component in pre_merge_data['data']:
                if component['type'] != "O":
                    component_data.append(component)
                    group_type += component['sub_type'] if 'sub_type' in component else component['type']
            data = {
                'type': "C",
                'sub_type': "Cg",
                'question_type': operation['operation'],
                'components': {
                    'data': component_data,
                    'group_type': "Og" + pre_merge_data['data'][1]['type'],
                    'relations': table,
                    'attributes': pre_merge_data['attributes'],
                    'expressions': pre_merge_data['expressions'],
                    'operations': [pre_merge_data['operations'][0]['operations'][1]]
                },
            }
            return data
        if pre_merge_data['group_type'] == "Question from complex aggregation":
            data = pre_merge_data['data'][-1]
            data['components']['data'].append(pre_merge_data['data'][0])
            for component in pre_merge_data['data']:
                if component['type'] == "C":
                    continue
                component_type = component['sub_type'] if 'sub_type' in component else component['type']
                data['components']['group_type'] += component_type
                if pre_merge_data['data'][0]['type'] == "R":
                    data['components']['relations'].append(pre_merge_data['data'][0])
                elif pre_merge_data['data'][0]['type'] == "A":
                    data['components']['attributes'].append(pre_merge_data['data'][0])
            return data
        if pre_merge_data['group_type'] == "Attribute with Expression":  # "(AE)|(EA)"
            # data = {'type': "E"} TODO
            # find out attribute is used in conditions of expression
            # if not used add in attributes & used attributes
            data = self.blank_merge(pre_merge_data['data'])
            return data
        if pre_merge_data['group_type'] == "Operation updation":  # "AOrE"
            expression = pre_merge_data['expressions'][0]
            operation = pre_merge_data['operations'][0]
            # find out attribute is used in conditions of expression
            # Update operation in conditions
            conditions = []
            # TODO attribute verificaion
            for condition in expression['conditions']:
                condition['operation'] = self.merger_op[operation['operation']][condition['operation']]
                conditions.append(condition)
            expression['conditions'] = conditions
            return expression

        if pre_merge_data['group_type'] == "Simple group":
            # TODO
            data = self.blank_merge(pre_merge_data['data'])  # {'type': "E"}
            return data

        if pre_merge_data['group_type'] == "Defined Period":
            data = {
                'type': "T", 'sub_type': "Tdp"
            }
            for time_data in pre_merge_data['data']:
                if time_data['sub_type'] == "Td":
                    data['definer'] = time_data['definer']
                if time_data['sub_type'] == "Tp":
                    data['period'] = time_data['period']
            return data
        if pre_merge_data['group_type'] == "Time Conditions":
            attribute = pre_merge_data['attributes'][0]
            if attribute['attribute_type'] != "time":
                raise NotImplementedError('check the question is well formulated and contact admin for support')
            used_attributes = [{'relation': attribute['relation'], 'attribute': attribute['attribute']}]
            tables = [attribute['relation']]
            display = 0
            time_data = pre_merge_data['data'][1]
            condition = self.condition_with_attribute(attribute, time_data, {'operation': "="})
            condition['type'] = "time"
            data = {
                'type': "E",
                'conditions': [condition],  # TODO expressions from values
                'used_attributes': used_attributes,
                'attributes': [],
                'table': tables
            }
            return data
        # If not in any of the translated groups
        # save the question in a sheet
        print "----------------------------------------------"
        print pre_merge_data['group_type']
        # raise NotImplementedError('Chec the question is well formulated and contact admin for support')

    def blank_merge_expressions(self, expressions):
        final_expression = {'type': "E", 'attributes': [],
                            'conditions': [], 'table': [], 'used_attributes': []}
        for expression in expressions:
            for relation in expression['table']:
                if relation not in final_expression['table']:
                    final_expression['table'].append(relation)
            for attribute in expression['attributes']:
                if attribute not in final_expression['attributes']:
                    final_expression['attributes'].append(attribute)
            for attribute in expression['attributes']:
                new_attr = {
                    'attribute': attribute['attribute'], 'relation': attribute['relation']}
                if new_attr not in final_expression['used_attributes']:
                    final_expression['used_attributes'].append(new_attr)
            final_expression['conditions'].extend(expression['conditions'])
        return final_expression

    def blank_merge(self, pre_mergeData):
        """ only if attributes, values & expressions are there
        """
        final_expression = {'type': "E", 'attributes': [],
                            'conditions': [], 'table': [], 'used_attributes': []}
        # segregate by type
        attributes = []
        expressions = []
        used_attributes = []
        for data in pre_mergeData:
            if 'relation' in data and data['relation'] not in final_expression['table']:
                final_expression['table'].append(data['relation'])
            if 'table' in data:
                for relation in data['table']:
                    if relation not in final_expression['table']:
                        final_expression['table'].append(relation)
            if data['type'] == "A":
                attributes.append(data)
            if data['type'] == "V":
                attribute = {
                    'type': "A",
                    'relation': data['relation'],
                    'attribute': data['attribute']
                }
                used_attributes.extend(attribute)
                expressions.append(self.expression_from_value(data))
            if data['type'] == "E":
                expressions.append(data)
                for used_attribute in data['used_attributes']:
                    if used_attribute not in final_expression['used_attributes']:
                        final_expression['used_attributes'].append(used_attribute)
                for attribute in final_expression['used_attributes']:
                    if attribute not in used_attributes:
                        used_attributes.append(attribute)
                # if 'relation' in data and data['relation'] not in final_expression['table']:
                #     final_expression['table'].append(data['relation'])
                # elif 'table' in data and data['table'] not in final_expression['table']:
                #     final_expression['table'].extend(data['table'])
        # if more than one attribute is present, add them in attributes
        if len(attributes) > 1:
            final_expression['attributes'].append(
                attribute for attribute in attributes not in final_expression['attributes'])
        if len(attributes) == 1:
            if not (len(used_attributes) == 1 and
                    attributes[0]['relation'] == used_attributes[0]['relation'] and
                    attributes[0]['attribute'] == used_attributes[0]['attribute']):
                final_expression['attributes'].append(attributes[0])
        # if values present make equivalence conditions update used attributes also
        # update tables

        # merge group expressions iteratively
        if len(expressions) == 0:
            return final_expression
        expressions.append(final_expression)
        return self.blank_merge_expressions(expressions)

    def expression_from_value(self, data):
        """ Form expression from value
        """
        return {
            'type': "E",
            'conditions': [{
                'operation': "=",
                'explicit': True,
                'LHS': {
                    'type': "A",
                    'relation': data['relation'],
                    'attribute': data['attribute'],
                    'explicit': False
                },
                'RHS': data
            }],
            'attributes': [],
            'table': [data['relation']],
            'used_attributes': [{'type': "A", 'relation': data['relation'], 'attribute': data['attribute']}]
        }

    def condition_from_value(self, data, operation):
        return {
            'operation': operation['operation'],
            'explicit': True,
            'LHS': {
                'type': "A",
                'relation': data['relation'],
                'attribute': data['attribute'],
                'explicit': False
            },
            'RHS': data
        }

    def condition_with_attribute(self, attribute, value, operation):
        return {
            'operation': operation['operation'],
            'explicit': True,
            'LHS': {
                'type': "A",
                'relation': attribute['relation'],
                'attribute': attribute['attribute'],
                'explicit': False
            },
            'RHS': value
        }

    def negate(self, data):
        if data['type'] == "V":
            return {
                'type': "E",
                'conditions': [{
                    'operation': "!=",
                    'explicit': True,
                    'LHS': {
                        'type': "A",
                        'relation': data['relation'],
                        'attribute': data['attribute'],
                        'explicit': False
                    },
                    'RHS': data
                }],
                'attributes': [],
                'table': [data['relation']],
                'used_attributes': [{'type': "A", 'relation': data['relation'], 'attribute': data['attribute']}]
            }
        if data['type'] == "E":
            for index in xrange(1, len(data['conditions'])):
                data['conditions'][index]['operation'] = self.merger_op['!'][data['conditions'][index]['operation']]
            return data
