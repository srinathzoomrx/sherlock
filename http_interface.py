import BaseHTTPServer
import SocketServer
import threading
import time
import urlparse
from translator import translator
import os
import json
import MySQLdb

HOST_NAME = 'localhost'  # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8080  # Maybe set this to 9000.

db = MySQLdb.connect("localhost", "root", "root", "Sherlock")
cursor = db.cursor()


class SherlockServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass


class QuestionHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def get_request_id(self):
        cursor.execute("SELECT MAX(id) FROM Request_Info")
        data = cursor.fetchall()
        request_id = data[0][0]
        if(request_id is None):
            request_id = 0
        return request_id + 1

    def write_into_DB(self, request_id, question, ambiguities, queries, running_time):
        db_writer = "INSERT INTO Request_Info (id, question, ambiguities, post_p_data, running_time) "
        db_writer += "values (" + str(request_id) + ", \'" + question + "\', \'"
        db_writer += json.dumps(ambiguities).replace("'", "\\'") + "\', \'" + json.dumps(queries).replace("'", "\\'") + "', "
        db_writer += str(running_time) + ");"
        cursor.execute(db_writer)
        cursor.execute("commit;")

    def write_into_DB_part2(self, request_id, usr_res, chosen_ppd, sql_query, writing_time):
        db_writer = "UPDATE Request_Info SET user_response = \'" + usr_res + "\' WHERE id = \'" + str(request_id) + "\';"
        cursor.execute(db_writer)
        db_writer = "UPDATE Request_Info SET chosen_post_p_data = \'" + json.dumps(
            chosen_ppd).replace("'", "\\'") + "\' WHERE id = \'" + str(request_id) + "\';"
        cursor.execute(db_writer)
        db_writer = "UPDATE Request_Info SET sql_query = \'" + sql_query + "\' WHERE id = \'" + str(request_id) + "\';"
        cursor.execute(db_writer)
        db_writer = "UPDATE Request_Info SET sql_writer_time = \'" + str(1) + "\' WHERE id = \'" + str(request_id) + "\';"
        cursor.execute(db_writer)
        cursor.execute("commit;")

    def get_info_from_DB(self, request_id):
        db_writer = "SELECT post_p_data, ambiguities FROM Request_Info WHERE id = " + str(request_id) + ";"
        cursor.execute(db_writer)
        data = cursor.fetchall()
        post_p_data = {}
        for row in data:
            post_p_data = row[0]
            ambiguities = row[1]
        return [json.loads(post_p_data), json.loads(ambiguities)]

    def do_GET(self):
        self.send_response(200)
        parse_result = urlparse.urlparse(self.path)
        print threading.currentThread().getName()
        queries = []
        query = urlparse.parse_qs(parse_result.query)
        # Checks the type of document request using content-type
        if self.headers.getheader('content-type') == 'application/json':
            if 'question' in query:
                self.send_header("Content-type", "application/json")
                self.end_headers()
                # try:
                start = time.time()
                translator_obj = translator()
                queries = translator_obj.queryFromQuestion(query['question'][0])
                running_time = time.time() - start
                if(len(translator_obj.ambiguities['data']) > 0):
                    request_id = self.get_request_id()
                    translator_obj.ambiguities['id'] = request_id
                    result = json.dumps(translator_obj.ambiguities)
                    self.wfile.write(result)
                    self.write_into_DB(
                        request_id,
                        query['question'][0],
                        translator_obj.ambiguities,
                        queries, running_time)
                else:
                    request_id = self.get_request_id()
                    self.wfile.write(json.dumps({'type': 'answer', 'data': []}))
                    self.write_into_DB(
                        request_id,
                        query['question'][0],
                        translator_obj.ambiguities,
                        queries, running_time)
                    start = time.time()
                    sql_query = translator_obj.return_sql_query(queries)
                    self.write_into_DB_part2(
                        request_id,
                        "None",
                        queries[0],
                        str(sql_query['query']),
                        time.time() - start)
                '''
                except Exception as e:
                    queries = json.dumps({"error": e.message})
                '''
                if(len(queries) > 100):
                    self.wfile.write(queries)

            elif 'user_response' in query:
                translator_obj = translator()
                options = query['user_response'][0].split('$')
                request_id = options[len(options) - 1]
                del options[len(options) - 1]
                post_p_data, ambiguities = self.get_info_from_DB(request_id)
                options = map(int, options)
                tot = []
                for i in range(len(ambiguities['data'])):
                    tot.append(len(ambiguities['data'][i]['options']))
                tot.append(1)
                locate_option = 0
                for i in range(len(options)):
                    mul_factor = 1
                    for j in range(i + 1, len(tot), 1):
                        mul_factor *= tot[j]
                    locate_option += mul_factor * options[i]

                start = time.time()
                sql_query = translator_obj.return_sql_query(post_p_data[locate_option])
                self.write_into_DB_part2(
                    request_id,
                    str(options),
                    post_p_data[locate_option],
                    str(sql_query['query']),
                    time.time() - start)
                # print translator_obj.ambi_phrases['data'][locate_option]
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({'type': 'answer', 'data': []}))

        else:
            if (self.path.endswith('.log')):
                self.send_header("Content-type", "text/text")
                self.end_headers()
                for line in reversed(open(self.path).readlines()):
                    self.wfile.write(line.rstrip() + "\n")

            elif(self.path.endswith('.js')):
                    self.send_header('Content-type', 'text/javascript')
                    self.end_headers()
                    f = open(os.getcwd() + '/scripts.js', 'r')
                    self.wfile.write(f.read())
                    f.close()

            else:
                self.send_header("Content-type", "text/html")
                self.end_headers()
                dash = open(os.getcwd() + '/index.html', 'r')
                self.wfile.write(dash.read())
                dash.close()


if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = SherlockServer((HOST_NAME, PORT_NUMBER), QuestionHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    httpd.serve_forever()
