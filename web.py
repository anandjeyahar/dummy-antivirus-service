
import hashlib
import json
import os
import random
import redis
import sys
import tornado
import tornado.httpserver
from tornado.options import define, options
from tornado.web import RequestHandler, Application, asynchronous

define('debug', default=1, help='hot deployment. use in dev only', type=int)
define('port', default=8888, help='run on the given port', type=int)

IMG_HASHES = 'img:hash:'
class AntiVirusHandler(RequestHandler):
    # for asychronous see example here .
    # http://www.tornadoweb.org/en/stable/web.html?highlight=asynchronous#tornado.web.asynchronous
    # @asynchronous
    def post(self):
        force = self.get_arguments('force', None)
        if not force:
            # Read the images
            imgBytes = self.request.files.get('file_inp')[0].body
            imgFileName = self.request.files.get('file_inp')[0].filename
            imgHash = hashlib.sha512(imgBytes).hexdigest()
            # Store result in redis for lookup of repeat images
            imgNew = redisConn.get(IMG_HASHES + ':' + imgHash)
            r = random.random()
            if r > 0.95:
                self.set_status(503)
                self.finish()
            if imgNew:
                result = True  if r < 0.2 else False
                redisConn.set(IMG_HASHES + ':' + imgHash, result)
            else:
                result = redisConn.get(IMG_HASHES + ':' + imgHash)
            self.set_status(200)
            self.finish({'valid': result })
        else:
            self.finish({ 'valid': force })
class Application(Application):
    def __init__(self):
        redisConn = redis.Redis(host='127.0.0.1',
                                port=6379, db=0)
        handlers = [
                (r'/', AntiVirusHandler),
                ]
        settings = dict(
            autoescape=None,  # tornado 2.1 backward compatibility
            debug=options.debug,
            gzip=True,
            xheaders=True,

            )
        settings.update({'static_path':'./static'})
        settings.update({'template_path': os.path.join(os.path.dirname(__file__), 'static', 'html')})
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    tornado.options.parse_command_line()
    App = Application()
    httpserver = tornado.httpserver.HTTPServer(App)
    httpserver.listen(port=options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
