from question_components_modified import question_components_modified
from sql_writer import sql_writer
from semantic_group import semantic_group
import copy
import os
import logging
from database import Database
import datetime
import json


class translator:
    def __init__(self):
        self.ambiguities = {}
        self.queries = []
        self.ques_comp_mod_obj = question_components_modified()
        self.sql_writer_obj = sql_writer()
        self.semantic_group_obj = semantic_group()
        self.database = Database({
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'sys',
            'raise_on_warnings': True,
        })
        logging.basicConfig(filename=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'logs/info.log'), level=logging.DEBUG)

    def queryFromQuestion(self, question):
        logging.info(str(datetime.datetime.now()) + " QUESTION: " + question)
        self.ques_comp_mod_obj.reset_variables()
        component_options = self.ques_comp_mod_obj.retrieve(question)
        self.ambiguities = self.ques_comp_mod_obj.ambiguities
        return component_options

    def return_sql_query(self, components):
        logging.info(components)
        query = "SELECT * from clinical_trials"
        component_string = json.dumps(components[0])
        # try:
        '''
        if components['type'] == "C":
            complex_queries = self.solve_complex_query(components)
            if not complex_queries:
                pass
            query = complex_queries
        else:
        '''
        query = self.sql_writer_obj.formQuery(component_string)
        logging.info("Query: " + query)
        if not query:
            pass
        # response = self.database.execute(query)
        queries = {"query": query, "response": "response", "components": component_string[0]}
        # except Exception as e:
        #     print e.message
        #     queries = {"query": query, "error": e.message, "components": component_string}

        logging.info(str(datetime.datetime.now()))
        logging.info("---------------------")
        return queries

    def solve_complex_query(self, question):
        component_string = json.dumps(question)
        if question['sub_type'] == "Cg":
            question['components']['group_type'] = self.semantic_group_obj.group_type(question['components']['group_type'])
            base_query = copy.deepcopy(question_components_modified.postProcessComponent(
                self.semantic_group_obj.merged_data(question['components'])
            ))
            for attribute in base_query['attributes']:
                if 'operation' in attribute:
                    attribute['alias'] = "result"
            derived = self.sql_writer_obj.formQuery(
                base_query
            )
            print "A = " + derived
            if question['question_type'] in ['MAX', 'MIN']:
                query = derived + " ORDER BY result "
                if question['question_type'] == "MAX":
                    query += "DESC "
                query += "LIMIT 1"
            else:
                query = "SELECT " + question['question_type'] + "(result) FROM (" + derived + ") as derived"
            response = self.database.execute(query)
            return {"query": query, "response": response, "components": component_string}

        if question['sub_type'] == "Cp":
            # percentage question
            question['components']['group_type'] = self.semantic_group_obj.group_type(question['components']['group_type'])
            base_query = copy.deepcopy(question_components_modified.postProcessComponent(question['components']['data'][0]))
            base_query['attributes'].append({'type': "String", 'field': "COUNT(*)"})
            if question['components']['data'][1]['type'] != "A":
                merged_data = self.semantic_group_obj.merged_data(question['components'])
                if not merged_data:
                    return
                query = self.sql_writer_obj.formQuery(base_query)
                response = self.database.execute(query)
                percent_components = question_components_modified.postProcessComponent(merged_data)
            else:
                if question['components']['data'][1]['relation'] not in question_components_modified.postProcessComponent(
                        question['components']['data'][0])['table']:
                    percent_components = question_components_modified.postProcessComponent(
                        self.semantic_group_obj.merged_data(question['components'])
                    )
                else:
                    percent_components = question_components_modified.postProcessComponent(question['components']['data'][0])
                percent_components['attributes'].append(question['components']['data'][1])
            if response[0][0] != 0:
                percent_components['attributes'].append({
                    'type': "String", 'field': "COUNT(*)*100/" + str(response[0][0]) + " as percent"
                })
                base_query['table'] = copy.deepcopy(percent_components['table'])
                query2 = self.sql_writer_obj.formQuery(percent_components)
                query = query + "; " + query2
        if response[0][0]:
            response = self.database.execute(query2)
        logging.info(query)
        return {"query": query, "response": response, "components": component_string}


def main():
    translator_obj = translator()
    queries = translator_obj.queryFromQuestion("india")
    print queries


if __name__ == '__main__':
    main()
    
