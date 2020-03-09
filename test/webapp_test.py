import sys 
sys.path.append('py')

import unittest 
from paste.fixture import TestApp
from oktest import ok as expect, test, todo, run as runTests   

from webapp import expose, Application, URLS, Index 
import webapp 


testApp = None

class DefaultSiteTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global testApp 
        Index.root = None
        app = Application(URLS, globals())
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



class ThirdLevel:
    @expose(contentType='text/html; charset=utf-8')
    def index(self):
        return '''ThirdLevel.index'''


class SecondLevelWithDefaultHandling:
    def __init__(self):
        self.third = ThirdLevel()

    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SecondLevelWithDefault.default'''

    def notexposed(self):
        return '''SecondLevelWithDefault.notexposed'''
     

class SecondLevelWithoutDefaultHandling:
    pass 

class SecondLevelNoIndexWithDefault:
    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SecondLevelNoIndexWithDefault.default'''


class SiteRoot:
    def __init__(self):
        self.withDefault = SecondLevelWithDefaultHandling()
        self.withoutDefault = SecondLevelWithoutDefaultHandling()
        self.noIndexWithDefault = SecondLevelNoIndexWithDefault() 

    @expose(contentType='text/html; charset=utf-8')
    def index(self):
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

        Index.root = SiteRoot()
        app = Application(URLS, globals())
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


if __name__ == '__main__':
    #unittest.main()
    runTests()
