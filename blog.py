import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import riak
import datetime

"""
http://docs.basho.com/riak/latest/dev/taste-of-riak/querying-python/ - samples of data
http://pragmaticbadger.com/latestnews/2010/nov/16/getting-started-riak-python/ - comments
https://riak-python-client.readthedocs.org/en/1.5-stable/tutorial.html

for keys in post_bucket.stream_keys():
    for key in keys:
        print('Deleting %s' % key)
        post_bucket.delete(key)
exit()
"""

 
client = riak.RiakClient(pb_port=8087, protocol='pbc')
post_bucket = client.bucket('Posts')
category_bucket = client.bucket('Categories')
post = {
    'post_id': 1,
    'name': "Black Hole",
    'author': "Wikipedia",
    'created_date': "2014-12-02 14:30:26",
    'is_active': '1',
    'category': 'News',
    'body': "A black hole is a region of spacetime from which gravity prevents anything, including light, "
            "from escaping. The theory of general relativity predicts that a sufficiently compact mass will "
            "deform spacetime to form a black hole."
}

category = {
    'post_id': 1,
    'category': 'News'
}
 
pb = post_bucket.new(str(post['post_id']), data=post)
pb.store()
cb = category_bucket.new(str(category['post_id']), data=category)
cb.store()

define("port", default=8000, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/add', AddPostHandler),
            (r'/post/(\d+)', PostHandler),
            (r'/edit/(\d+)', EditPostHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        query = riak.RiakMapReduce(client).add('Posts')
        query.map("""function(v)
                        { var data = JSON.parse(v.values[0].data);
                        if(data.is_active == 1)
                            { return [[v.key, data]]; }
                        return []; }""")
        self.render(
            "index.html",
            title="Home Page",
            data=query.run(),
        )


class PostHandler(tornado.web.RequestHandler):
    def get(self, post_id):
        widget = post_bucket.get(post_id).data
        widget['category'] = category_bucket.get(post_id).data
        self.render("single.html", data=widget, key=post_id)

    def delete(self, post_id):
        post = post_bucket.get(post_id)
        post.delete()
        self.redirect('/')


class EditPostHandler(tornado.web.RequestHandler):
    def get(self, post_id):
        post = post_bucket.get(post_id)
        self.render('edit.html', data=post.data, key=post_id)

    def post(self, post_id):
        name = self.get_argument('name')
        body = self.get_argument('body')
        author = self.get_argument('author')
        is_active = self.get_argument('is_active')
        category = self.get_argument('category')
        entry = post_bucket.get(post_id)
        entry.data['name'] = name
        entry.data['body'] = body
        entry.data['author'] = author
        entry.data['is_active'] = is_active
        cat = category_bucket.get(post_id)
        cat.data = category
        cat.store()
        self.redirect("/post/%s" % post_id)


class AddPostHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('add_post.html')

    def post(self):
        name = self.get_argument('name')
        body = self.get_argument('body')
        author = self.get_argument('author')
        category = self.get_argument('category')
        d = {'name': name,
             'body': body,
             'author': author,
             'created_date': str(datetime.date.today()),
             'type': 'post',
             'is_active': '1'}
        new_key = sorted(post_bucket.get_keys())
        k = int(new_key[-1]) + 1
        entry = post_bucket.new(str(k), data=d)
        entry.store()
        cat = category_bucket.new(str(k), data=category)
        cat.store()
        self.redirect('/post/%s' % entry.key)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()