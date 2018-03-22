from semantic_group import semantic_group
from token_handler import token_handler
from nltk.parse.stanford import StanfordParser
import nltk.tree
import copy


class question_components_modified:
    def __init__(self):
        self.token_handler_obj = token_handler()
        self.semantic_group_obj = semantic_group()
        jar_file = '/root/Stanford_CoreNLP/stanford-corenlp-3.8.0.jar'
        model_path = '/root/Stanford_CoreNLP/stanford-corenlp-3.8.0-models.jar'
        self.parser = StanfordParser(jar_file, model_path)
        self.ambiguities = {'type': 'options', 'data': []}
        self.ambi_phrases = [[]]
        self.index = -1  # Variable used in the populate_ambiguites() definition

    def reset_variables(self):
        self.ambiguities = {'type': 'options', 'data': []}
        self.ambi_phrases = [[]]
        self.index = -1

    def retrieve(self, question):
        """
        From the question retrieve necessary components as expression
        Argument - str - question

        return expression
        """
        components = []
        parsed_tree = self.parser.raw_parse(question).next()
        self.populate_ambiguities(parsed_tree)
        query_components = self.buildComponents(parsed_tree)
        for option in query_components:
            components.append(self.postProcessComponents(option))
        return components

    def populate_ambiguities(self, node, s=0):
        start = s
        for element in node:
            if type(element) is nltk.Tree:
                phrase = " ".join(element.leaves())
                token_info = self.token_handler_obj.get_token_details(phrase)
                if isinstance(token_info, list):
                    options = []
                    for info in token_info:
                        if info['type'] == 'V':
                            options.append(info['value'] + ' as a ' + info['domain'])
                        elif info['type'] == 'A':
                            options.append(phrase + ' as an element of ' + info['relation'])
                        elif info['type'] == 'R':
                            options.append(phrase + ' as a ' + phrase)
                    data = {
                        'value': phrase,
                        'start': start,
                        'options': options,
                    }
                    self.index += 1
                    self.ambiguities['data'].append(data)
                    start = start + len(phrase) + 1
                    continue
                self.populate_ambiguities(element, start)
                start = start + len(phrase) + 1

    def postProcessComponents(self, component_options):
        if not isinstance(component_options, list):
            component_options = [component_options]
        processed_components = []
        for components in component_options:
            processed_components.append(self.postProcessComponent(components))
        return processed_components

    def postProcessComponent(self, components):
        if components['type'] == "R":
            return {'type': "E", 'attributes': [], 'conditions': [], 'table': [components['relation']]}
        if components['type'] == "A":
            if 'sub_type' in components and components['sub_type'] == "Ax":
                attributes = components['attributes']
                tables = []
                for attribute in attributes:
                    if attribute['relation'] not in tables:
                        tables.append(attribute['relation'])
                return {'type': "E", 'attributes': attributes, 'conditions': [], 'table': tables}
            return {'type': "E", 'attributes': [components], 'conditions': [], 'table': [components['relation']]}
        return components

    def merge_operations(self, op1, op2):
        """
        Merge two operations
        Arguement - operation - op1
                  - operation - op2

        Return operation
        """
        if (op1['operation'] not in self.semantic_group_obj.merger_op or op2['operation'] not in self.semantic_group_obj.merger_op[op1['operation']]):
            return False
        return {
            'type': "O",
            'operation': self.semantic_group_obj.merger_op[op1['operation']][op2['operation']],
            'token': op1['token'] + " " + op2['token'],
            'explicit': True  # assuming both would be explicit
        }

    def buildComponents(self, node):
        pre_mergeData = [[]]
        processingOperations = [[]]
        expressions = [[]]
        attributes = [[]]
        relations = [[]]
        query_components = []

        solutions_count = 1
        for element in node:
            if type(element) is nltk.Tree:
                phrase = " ".join(element.leaves())
                token_info = self.token_handler_obj.get_token_details(phrase)
                if token_info is False:
                    # The phrase is not found in the dictionary
                    # Go down the tree to find smaller phrases or just a word
                    returned_comp = self.buildComponents(element)
                    # The query_component of this element's child is received in the returned_comp
                    if len(returned_comp) == 1:
                        # pre_mergeData = returned_comp
                        for i in range(solutions_count):
                            pre_mergeData[i].append(returned_comp[0])
                            if returned_comp[0]['type'] == 'A':
                                attributes[i].append(returned_comp[0])
                            elif returned_comp[0]['type'] == 'R':
                                relations[i].append(returned_comp[0])
                            elif returned_comp[0]['type'] == 'E':
                                expressions[i].append(returned_comp[0])

                    elif len(returned_comp) == 0:
                        # Empty query_components of the child that has returned
                        continue

                    else:
                        solutions_count = len(returned_comp)
                        # The increase in the number of possiblities is updated
                        pre_mergeData = [copy.deepcopy(z) for z in pre_mergeData for i in range(solutions_count)]
                        processingOperations = [copy.deepcopy(z) for z in processingOperations for i in range(solutions_count)]
                        expressions = [copy.deepcopy(z) for z in expressions for i in range(solutions_count)]
                        relations = [copy.deepcopy(z) for z in relations for i in range(solutions_count)]
                        attributes = [copy.deepcopy(z) for z in attributes for i in range(solutions_count)]
                        # Hence, increaseing the size of pre_megredData and query_components to size of solutions count
                        solutions_count = len(pre_mergeData)
                        for i in range(solutions_count):
                            j = i % len(returned_comp)
                            # for r in returned_comp[j]:
                            pre_mergeData[i].append(returned_comp[j])
                            if returned_comp[j]['type'] == 'A':
                                attributes[i].append(returned_comp[j])
                            elif returned_comp[j]['type'] == 'R':
                                relations[i].append(returned_comp[j])
                            elif returned_comp[j]['type'] == 'E':
                                expressions[i].append(returned_comp[j])
                        # Hence, increaseing
                    # The query_component of the child is copied to pre_mergedData of the parent
                    # for finding if there are any meaningful group structure

                elif token_info is None:
                    # The phrase or word is a stopword
                    continue  # Do Nothing
                elif isinstance(token_info, list):
                    # Various interpretations are possible
                    solutions_count = solutions_count * len(token_info)
                    pre_mergeData = [copy.deepcopy(z) for z in pre_mergeData for i in range(len(token_info))]
                    processingOperations = [copy.deepcopy(z) for z in processingOperations for i in range(len(token_info))]
                    expressions = [copy.deepcopy(z) for z in expressions for i in range(len(token_info))]
                    attributes = [copy.deepcopy(z) for z in attributes for i in range(len(token_info))]
                    relations = [copy.deepcopy(z) for z in relations for i in range(len(token_info))]
                    query_components = [copy.deepcopy(z) for z in query_components for i in range(len(token_info))]
                    self.ambi_phrases = [copy.deepcopy(z) for z in self.ambi_phrases for i in range(len(token_info))]
                    for i in range(len(self.ambi_phrases)):
                        j = i % len(token_info)
                        if token_info[j]['type'] == 'V':
                            self.ambi_phrases[i].append(token_info[j]['value'] + ' as a ' + token_info[j]['domain'])
                        elif token_info[j]['type'] == 'A':
                            self.ambi_phrases[i].append(phrase + ' as an element of ' + token_info[j]['relation'])
                        elif token_info[j]['type'] == 'R':
                            self.ambi_phrases[i].append(phrase + ' as a ' + phrase)
                else:
                    # Only one interpretation
                    token_info = [token_info]

                if(token_info is not False and token_info is not None):
                    # Append the details only if the phrase is found in the dictionary
                    for i in range(solutions_count):
                        j = i % len(token_info)
                        if token_info[j]['type'] == "R":
                            if 'relation' not in token_info[j]:
                                token_info[j]['relation'] = phrase
                            pre_mergeData[i].append(token_info[j])
                            relations[i].append(token_info[j])

                        elif token_info[j]['type'] == "A":
                            if 'attribute' not in token_info[j]:
                                token_info[j]['attribute'] = phrase
                            pre_mergeData[i].append(token_info[j])
                            attributes[i].append(token_info[j])

                        elif token_info[j]['type'] == "E":
                            pre_mergeData[i].append(token_info[j])
                            expressions[i].append(token_info[j])

                        elif token_info[j]['type'] in ["C", "I", "T"]:
                            pre_mergeData[i].append(token_info[j])

                        elif token_info[j]['type'] == "V":
                            if 'value' not in token_info[j]:
                                token_info[j]['value'] = phrase
                            pre_mergeData[i].append(token_info[j])

                        elif token_info[j]['type'] == "A":
                            if 'attribute' not in token_info[j]:
                                token_info[j]['attribute'] = phrase
                            pre_mergeData[i].append(token_info[j])
                            attributes[i].append(token_info[j])

                        elif token_info[j]['type'] == "O":
                            if (len(pre_mergeData[i]) != 0 and
                                    (pre_mergeData[i][-1]['type'] == "O") and
                                    pre_mergeData[i][-1]['sub_type'] != "Oq"):
                                processingOperations[i].pop()
                                merged_operation = self.merge_operations(token_info[j], pre_mergeData[i][-1])
                                if not merged_operation:
                                    pre_mergeData[i].append(token_info[j])
                                    processingOperations[i].append(token_info[j])

                                else:
                                    pre_mergeData[i].pop()
                                    # to identify operation seperated by operands
                                    processingOperations[i].append(self.merge_operations)
                                    pre_mergeData[i].append(merged_operation)
                            else:
                                pre_mergeData[i].append(token_info[j])
                                processingOperations[i].append(token_info[j])
                            processingOperations[i][-1]['position'] = len(pre_mergeData[i]) - 1
                        else:
                            pre_mergeData[i].append(token_info[j])

        # weight = 0
        for i in range(solutions_count):
            if len(pre_mergeData[i]) == 0:
                # No pre_mergeData Exists in the node
                pass
            elif len(pre_mergeData[i]) == 1:
                # if only one element is present forward to previous level
                query_components.append(pre_mergeData[i][0])

            else:
                # Parse through pre-merge data to identify group type & form expressions
                group_structure = []
                for token_info in pre_mergeData[i]:
                    if 'sub_type' in token_info:
                        group_structure.append(token_info['sub_type'])
                    else:
                        group_structure.append(token_info['type'])

                group_type = self.semantic_group_obj.group_type(''.join(group_structure))
                merged_data = self.semantic_group_obj.merged_data({
                    'data': pre_mergeData[i],
                    'group_type': group_type,
                    'operations': processingOperations[i],
                    'attributes': attributes[i],
                    'relations': relations[i],
                    'expressions': expressions[i]
                })
                # current_weight = 0
                if merged_data is not False and merged_data is not None:
                    '''
                    if 'table' in merged_data:
                        current_weight = len(merged_data['table'])
                    if len(query_components) == 0 or weight > current_weight:
                        weight = current_weight
                        query_components = [merged_data]
                        pass
                    '''
                    query_components.append(merged_data)
        return query_components


def main():
    question = "players whose name is kohli"
    print question
    obj = question_components_modified()
    try:
        components = obj.retrieve(question)
        for component in components:
            print component
            print
    except Exception, e:
        print "There was some error!!! Handled Safley"
        print "Error message:", e.message


if __name__ == '__main__':
    main()
