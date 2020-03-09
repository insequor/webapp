import sys 
sys.path.append('py')

import unittest 
from paste.fixture import TestApp
from oktest import ok as expect, test, main as runTests   

from webapp import expose, Application, URLS, Index 
import webapp 

class FirstSiteTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Application(URLS, globals())
        middleware = []
        cls.testApp = TestApp(app.wsgifunc(*middleware))

    @classmethod
    def tearDownClass(cls):
        pass 

    @test("asking for the root url returns the missing page information")
    def _(self):
        res = self.testApp.get('/')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /'

    @test("asking for a URL other than the root url returns the missing page information")
    def _(self):
        res = self.testApp.get('/missing/page')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /missing/page'

    @test("asking for a URL with parameters returns missing page info without the parameters")
    def _(self):
        res = self.testApp.get('/missing/page?param=1&param=2')
        expect(res.status) == 200
        expect(res.body) == b'Missing Page: /missing/page'

    @test("it is possible to replace the global default handler")
    def _(self):
        oldHandler = webapp.global_default

        @expose(contentType='text/html; charset=utf-8')
        def my_default():
            return 'Custom global default handler'

        webapp.global_default = my_default
        res = self.testApp.get('/missing/page?param=1&param=2')
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


class SiteRoot:
    def __init__(self):
        self.withDefault = SecondLevelWithDefaultHandling()
        self.withoutDefault = SecondLevelWithoutDefaultHandling() 

    @expose(contentType='text/html; charset=utf-8')
    def index(self):
        return '''SiteRoot.index'''

    @expose(contentType='text/html; charset=utf-8')
    def page(self):
        return '''SiteRoot.page'''

    @expose(contentType='text/html; charset=utf-8')
    def default(self):
        return '''SiteRoot.default'''
    


class SecondSiteTest (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Index.root = SiteRoot()
        app = Application(URLS, globals())
        middleware = []
        cls.testApp = TestApp(app.wsgifunc(*middleware))

    @classmethod
    def tearDownClass(cls):
        pass 

    @test("asking for root URL returns the top level Index")
    def _(self):
        res = self.testApp.get('/')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.index'

    @test("asking for index page at top level will mapped to the index page")
    def _(self):
        res = self.testApp.get('/index')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.index'

    @test("asking for a specific top level URL returns the mapped page")
    def _(self):
        res = self.testApp.get('/page')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.page'

    @test("asking for a missing top level URL returns the default page from top level")
    def _(self):
        res = self.testApp.get('/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.default'

    @test("asking a missing page at second level returns the default handler of that level")
    def _(self):
        res = self.testApp.get('/withDefault/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'

    @test("asking a missing page at second level without default handler returns the last known default handler")
    def _(self):
        res = self.testApp.get('/withoutDefault/missingpage')
        expect(res.status) == 200
        expect(res.body) == b'SiteRoot.default'

    
    @test('If a functions is not exposed, URL mapping is not done and last known default is returned')
    def _(self):
        res = self.testApp.get('/withDefault/notexposed')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'

    @test('Requested a third level URL with missing second level returns the global handler')
    def _(self):
        res = self.testApp.get('/withDefault/missingpage/third')
        expect(res.status) == 200
        expect(res.body) == b'SecondLevelWithDefault.default'


if __name__ == '__main__':
    unittest.main()
    #runTests()
    #run(DefaultSiteTest, CustomSiteTest)
