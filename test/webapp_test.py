import sys 
sys.path.append('./')

import unittest 
from paste.fixture import TestApp
from oktest import ok as expect, test, todo, run as runTests   

from webapp import expose, Application, Site 
import webapp 


testApp = None
app = None

class DefaultSiteTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global testApp, app
        app = Application(root=None, urls=None, globals=globals())
        middleware = []
        testApp = TestApp(app.wsgifunc(*middleware))

    @classmethod
    def tearDownClass(cls):
        pass 

    @test("asking for the root url returns the missing page information")
    def _(self):
        res = testApp.get('/')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /'

    @test("asking for a URL other than the root url returns the missing page information")
    def _(self):
        res = testApp.get('/missing/page')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /missing/page'

    @test("asking for a URL with parameters returns missing page info without the parameters")
    def _(self):
        res = testApp.get('/missing/page?param=1&param=2')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /missing/page'

    @test("it is possible to replace the global default handler")
    def _(self):
        oldHandler = webapp.global_default

        @expose(contentType='text/html; charset=utf-8')
        def my_default():
            return 'Custom global default handler'

        webapp.global_default = my_default
        res = testApp.get('/missing/page?param=1&param=2')
        expect(res.status) == 200
        expect(res.body) == b'Custom global default handler'

        webapp.global_default = oldHandler

    @test("default site returns an empty site map")
    def _(_):
        expect(app.sitemap) == []



class ThirdLevel(Site):
    @expose(contentType='text/html; charset=utf-8')
    def index(self):
        return '''ThirdLevel.index'''


class SecondLevelWithDefaultHandling(Site):
    def __init__(self):
        self.third = ThirdLevel()

    @expose(contentType='text/html; charset=utf-8')
    def index(self):
        return '''SecondLevelWithDefault.index'''

    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SecondLevelWithDefault.default'''

    def notexposed(self):
        return '''SecondLevelWithDefault.notexposed'''
     

class SecondLevelWithoutDefaultHandling(Site):
    pass 

class SecondLevelNoIndexWithDefault(Site):
    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SecondLevelNoIndexWithDefault.default'''


class SiteRoot(Site):
    def __init__(self):
        self.noIndexWithDefault = SecondLevelNoIndexWithDefault()
        self.withDefault = SecondLevelWithDefaultHandling()
        self.withoutDefault = SecondLevelWithoutDefaultHandling()
         

    @expose(contentType='text/html; charset=utf-8')
    def index(self):
        '''Root page'''
        return '''SiteRoot.index'''

    @expose(contentType='text/html; charset=utf-8')
    def page(self):
        return '''SiteRoot.page'''

    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SiteRoot.default'''
    


class CustomSiteTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global testApp 
        global app

        app = Application(root=SiteRoot(), urls=None, globals=globals())
        middleware = []
        
        testApp = TestApp(app.wsgifunc(*middleware))

    @classmethod
    def tearDownClass(cls):
        pass 

    @test("asking for root URL returns the top level Index")
    def _(self):
        res = testApp.get('/')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.index'

    @test("asking for index page at top level will mapped to the index page")
    def _(self):
        res = testApp.get('/index')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.index'

    @test("asking for a specific top level URL returns the mapped page")
    def _(self):
        res = testApp.get('/page')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.page'

    @test("asking for a missing top level URL returns the default page from top level")
    def _(self):
        res = testApp.get('/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.default'

    @test("asking a missing page at second level returns the default handler of that level")
    def _(self):
        res = testApp.get('/withDefault/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'

    @test("asking a missing page at second level without default handler returns the last known default handler")
    def _(self):
        res = testApp.get('/withoutDefault/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.default'

    @test("Last known default handler is used of child root is requested and no index and default handlers available")
    def _(self):
        res = testApp.get('/withoutDefault')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.default'

    
    @test('If a functions is not exposed, URL mapping is not done and last known default is returned')
    def _(self):
        res = testApp.get('/withDefault/notexposed')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'

    @test('Requested a third level URL with missing second level returns the global handler')
    def _(self):
        res = testApp.get('/withDefault/missingpage/third')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'

    @test('Default handler of a child is used if child root is requested and no index handler found')
    def _(self):
        res = testApp.get('/noIndexWithDefault')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelNoIndexWithDefault.default'

    @test("webapp returns sitemap based on the given siteroot")
    def _(_):
        refSiteMap = [
            {'url': '/',
             'handler': 'SiteRoot',
             'description': 'Root page'},
            {'url': '/default',
             'handler': 'SiteRoot',
             'description': ''},
            {'url': '/index',
             'handler': 'SiteRoot',
             'description': 'Root page'},
            
            {'url': '/noIndexWithDefault/default',
             'handler': 'SecondLevelNoIndexWithDefault',
             'description': ''},

            {'url': '/page',
             'handler': 'SiteRoot',
             'description': ''},
            {'url': '/withDefault',
             'handler': 'SecondLevelWithDefaultHandling',
             'description': ''},
            {'url': '/withDefault/default',
             'handler': 'SecondLevelWithDefaultHandling',
             'description': ''},
            {'url': '/withDefault/index',
             'handler': 'SecondLevelWithDefaultHandling',
             'description': ''},
            {'url': '/withDefault/third',
             'handler': 'ThirdLevel',
             'description': ''},
            {'url': '/withDefault/third/index',
             'handler': 'ThirdLevel',
             'description': ''}
        ]
        expect(app.sitemap) == refSiteMap
    
    @test("Last known default handler is returned if top level url is mapped to an index page but it is not available")
    @todo 
    def _(_):
        expect(True) == False 

    @test("Last known default handler is returned if a default handler is found but it is not exposed")
    @todo 
    def _(_):
        expect(True) == False 


    @test("An absolute missing page handler is returned if global default handler is replaced but it is not exposed")
    @todo 
    def _(_):
        expect(True) == False 


    @test("Test that a callable can be set as a root location rather than a site object")
    @todo 
    def _(_):
        expect(True) == False 


class ParameterMappingTest:
    @test("URL Parameters are detected and passed to the handler automatically")
    @todo 
    def _(_):
        expect(True) == False 

if __name__ == '__main__':
    #unittest.main()
    runTests()
