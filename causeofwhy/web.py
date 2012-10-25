# Copyright (C) 2012 Brian Wesley Baugh
"""Web interface allowing users to submit queries and get a response."""
import os
import multiprocessing

import tornado.ioloop
import tornado.web
import tornado.httpserver

import answer_engine
from answer_engine import AnswerEngine


# How many page worker threads to use
NUMBER_OF_PROCESSES = max(1, multiprocessing.cpu_count() - 1)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class QueryHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.pool = self.application.settings.get('pool')
        self.index = self.application.settings.get('index')

    def prepare(self):
        self.query = None
        self.num_top = None
        self.ans_eng = None

    @tornado.web.asynchronous
    def get(self):
        self.query = self.get_argument('q')
        num_top = int(self.get_argument('top', default=10))
        start = int(self.get_argument('start', default=0))
        self.ans_eng = AnswerEngine(self.index, self.query, start, num_top)
        self.pool.apply_async(answer_engine.get_answers, (self.ans_eng,),
                              callback=self.callback)

    def callback(self, answers):
        self.render("answer.html",
                    query=self.query,
                    ir_query=' '.join(self.ans_eng.ir_query),
                    num_pages=self.ans_eng.num_pages,
                    answers=answers)


def main(index):
    pool = multiprocessing.Pool(NUMBER_OF_PROCESSES)
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/cause/", QueryHandler),
        ], template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        index=index,
        pool=pool)
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
