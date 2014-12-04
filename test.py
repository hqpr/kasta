from tornado.testing import AsyncTestCase, AsyncHTTPTestCase
from blog import Application
from tornado.test import httpserver_test
from tornado.test import web_test
from tornado.wsgi import WSGIApplication, WSGIContainer, WSGIAdapter
from wsgiref.validate import validator
try:
    from tornado import gen
    from tornado.httpclient import AsyncHTTPClient
    from tornado.httpserver import HTTPServer
    from tornado.simple_httpclient import SimpleAsyncHTTPClient
    from tornado.ioloop import IOLoop, TimeoutError
    from tornado import netutil
    from tornado.process import Subprocess
except ImportError:
    AsyncHTTPClient = None
    gen = None
    HTTPServer = None
    IOLoop = None
    netutil = None
    SimpleAsyncHTTPClient = None
    Subprocess = None
 
 
class MyHTTPTest(AsyncHTTPTestCase):
    def get_app(self):
        return Application()
 
    def test_homepage(self):
        self.http_client.fetch(self.get_url('/'), self.stop)
 
 
class WSGIConnectionTest(httpserver_test.HTTPConnectionTest):
    def get_app(self):
        return WSGIContainer(validator(WSGIApplication(self.get_handlers())))
 
    def wrap_web_tests_adapter():
        result = {}
        for cls in web_test.wsgi_safe_tests:
            class WSGIAdapterWrappedTest(cls):
                def get_app(self):
                    self.app = Application(self.get_handlers(),
                                           **self.get_app_kwargs())
                    return WSGIContainer(validator(WSGIAdapter(self.app)))
            result["WSGIAdapter_" + cls.__name__] = WSGIAdapterWrappedTest
        return result
 
 
class MyTestCase2(AsyncTestCase):
    def test_http_fetch(self):
        client = AsyncHTTPClient(self.io_loop)
        client.fetch("http://127.0.0.1:8000/", self.stop)
        response = self.wait()
        # Test contents of response
        self.assertIn("blog", response.body)