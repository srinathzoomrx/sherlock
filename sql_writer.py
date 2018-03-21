from model_opt import model_opt


class sql_writer:
    def __init__(self):
        pass

    def formQuery(self, components):
        if len(components['table']) == 0:
            return False
        query = "SELECT "
        # print components['attributes']
        attributes = []
        grp_attributes = []
        conditions = {}
        having = {}
        if len(components['attributes']) == 0:
            query = query + "*"
        else:
            for attribute in components['attributes']:
                if attribute['type'] is "String":
                    attributes.append(attribute['field'])
                    continue
                field = attribute['relation'] + "." + attribute['attribute']
                if attribute['attribute'] == "*":
                    field = "*"
                if 'operation' in attribute:
                    alias = attribute['alias'] if ('alias' in attribute) else None
                    attributes.append(
                        self.customField(field, attribute['operation'], alias))
                else:
                    grp_attributes.append(field)
                    attributes.append(field)
            query = query + (",".join(attributes))
        # TABLES
        query += " FROM "
        query += self.relations(components['table'])
        # CONDITIONS Handling
        if len(components['conditions']) != 0:
            agg_functions = ["AVG(", "SUM(", "MAX(", "MIN(", "COUNT("]
            for condition in components['conditions']:
                if 'type' in condition and condition['type'] == "time":
                    if '_stringified' not in conditions:
                        conditions['_stringified'] = []
                    conditions['_stringified'].append(self.period_condition(condition))
                    continue
                rhs_operands = self.operand_definition(condition['RHS'])
                lhs_operands = self.operand_definition(condition['LHS'])
                operation = condition['operation']
                for lhs_operand in lhs_operands:
                    for rhs_operand in rhs_operands:
                        if (any(operation for operation in agg_functions
                            if operation in lhs_operand) or
                                any(operation for operation in agg_functions
                                    if operation in lhs_operand)):
                            # aggregation in having
                            if lhs_operand not in having:
                                having[lhs_operand] = {}
                            if operation not in having[lhs_operand]:
                                having[lhs_operand][operation] = []
                            having[lhs_operand][operation].append(rhs_operand)
                        else:
                            if lhs_operand not in conditions:
                                conditions[lhs_operand] = {}
                            if operation not in conditions[lhs_operand]:
                                conditions[lhs_operand][operation] = []
                            conditions[lhs_operand][operation].append(rhs_operand)
        if conditions:
            query = query + " WHERE " + self.formConditionStatement(conditions)
        if having:
            query = query + " GROUP BY " + (
                ",".join(grp_attributes)) + " HAVING " +\
                self.formConditionStatement(having)
        elif grp_attributes and len(grp_attributes):
            query = query + " GROUP BY " + (",".join(grp_attributes))
        return query

    def formConditionStatement(self, conditions):
        query = ""
        flag = 0
        for field, condition in conditions.iteritems():
            if field == "_stringified":
                for stringified_condition in condition:
                    if flag > 0:
                        query = query + "AND "
                    flag = 1
                    query = query + stringified_condition
                continue
            if flag > 0:
                query = query + "AND "
            flag = 1
            for operation, values in condition.iteritems():
                if flag > 1:
                    query = query + "OR "
                flag = 2
                query = query + "("
                if operation == "=":
                    if len(values) > 1:
                        query = query + field + \
                            " IN (" + ",".join(values) + ") "
                    else:
                        query = query + field + " = " + ",".join(values) + " "
                elif operation == "!=" and len(values) > 1:
                    query = query + field + \
                        " NOT IN (" + ",".join(values) + ") "
                elif operation == "!=":
                    query = query + field + " != " + ",".join(values) + " "
                else:
                    query = query + field + " " +\
                        operation + " " + ",".join(values) + " "
                query = query + ") "
        return query

    def period_condition(self, condition):
        if 'definer' not in condition['RHS']:
            period_translator = {
                'yesterday': {'definer': 'last', 'period': 'DATE'},
                'today': {'definer': 'this', 'period': 'DATE'},
                'tomorrow': {'definer': 'next', 'period': 'DATE'}
            }
            condition['RHS']['definer'] = period_translator[
                condition['RHS']['definer']]
            condition['RHS']['period'] = period_translator[
                condition['RHS']['period']]
        # query_period = {
        #     'month': "MONTH",
        #     'quarter': "QUARTER",
        #     'week': "WEEK",
        # }
        hierarchy = {
            'DATE': ['DATE', 'MONTH', 'YEAR'],
            'WEEK': ['WEEK', 'YEAR'],
            'MONTH': ['MONTH', 'YEAR'],
            'QUARTER': ['QUARTER', 'YEAR'],
            'YEAR': ['YEAR']
        }
        period = condition['RHS']['period']
        lhs_operands = self.operand_definition(condition['LHS'])
        condition_query = ""
        operand_flag = 0
        for lhs_operand in lhs_operands:
            if operand_flag > 0:
                condition_query = condition_query + " AND "
            operand_flag = 1
            hierarchy_flag = 0
            for query_period in hierarchy[period.upper()]:
                if hierarchy_flag > 0:
                    condition_query = condition_query + " AND "
                hierarchy_flag = 1
                definer_suffix = ""
                if condition['RHS']['definer'] == "last":
                    definer_suffix = " - INTERVAL 1 " + period
                elif condition['RHS']['definer'] == "next":
                    definer_suffix = " + INTERVAL 1 " + period
                query = query_period + "(" + lhs_operand + ") = "
                query = query + query_period + "(curdate()" + definer_suffix + ")"
                condition_query = condition_query + "(" + query + ")"
            condition_query = "(" + condition_query + ")"
        return "(" + condition_query + ")"

    def operand_definition(self, condition_rhs):
        if not isinstance(condition_rhs, list):
            condition_rhs = [condition_rhs]
        rhs = []
        for element in condition_rhs:
            value = self.query_values(element)
            if isinstance(value, list):
                rhs.extend(value)
                continue
            rhs.append(value)
        return rhs

    def query_values(self, element):
        # elements can be of type A, Ag, Ax, I, Ix, V
        if element['type'] == "A":
            if 'sub_type' not in element:
                return self.query_field(element)

            if element['sub_type'] == "Ag":
                return self.customField(
                    self.query_field(element), element['operation'], None)

            if element['sub_type'] == "Ax":
                values = []
                for attribute in element['attributes']:
                    values.append(self.query_field(attribute))
                return values
        if element['type'] == "I":
            if 'sub_type' not in element:
                return element['number']
            if element['type'] == "Ix":
                numbers = []
                for number in element['numbers']:
                    numbers.append(number['number'])
                return numbers
        if element['type'] == "V":
            return '"' + element['value'] + '"'
        return False

    def query_field(self, attribute):
        return attribute['relation'] + "." + attribute['attribute']

    def customField(self, field, operation, alias):
        if operation['operation'] in ['AVG', 'MAX', 'MIN', 'SUM', 'COUNT']:
            field_name = operation['operation'] + '(' + field + ')'
            if alias:
                field_name = field_name + " as " + alias
            return field_name
        return field

    def relations(self, tables):
        """
        Form the relation base for the query to work
        Argument - list - tables

        Return str - [joined] tables
        """
        resource = model_opt()
        # get needed tables from model for the query
        relations = resource.getPathRelations(tables)
        # loop through the array through form relation
        query = ""
        if(relations[0][1] is None):
            query = relations[0][0]
        else:
            for i in range(len(relations)):
                query = query + '('
            query = query + relations[0][0]
            for relation in relations:
                query = query + "\nINNER JOIN " + relation[1] + " ON " + relation[2]
                query = query + ')'
        return query + " "


def main():
    obj = sql_writer()
    query = obj.relations(['balls', 'players', 'matches'])
    print query


if __name__ == '__main__':
    main()
