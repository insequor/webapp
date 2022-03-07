

# -*- coding: iso-8859-15 -*-

__license__ = '''
MIT License

Copyright (c) 2020 Ozgur Yuksel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

__doc__ = '''Please see https://github.com/insequor/webapp for details about this script
'''

__version__ = "0.1"
__author__ = [
    "Ozgur Yuksel <ozgur@insequor.com>"
]
__license__ = "MIT License"

import os
from inspect import signature 
from typing import List
from io import BytesIO
import gzip
from urllib.parse import unquote

import web


def defaultCORSOption():
    envVar = os.environ.get("WEBAPP_DEFAULT_CORS_OPTION", "")
    return envVar if envVar != "" else None


class expose:
    def __init__(self, contentType: str, 
                 contentEncoding: str=None, 
                 enableCORS: str=defaultCORSOption(), 
                 methods: List[str]=["GET", "POST"]):  # OPTIONS WILL BE ADDED AUTOMATICALLY
        self.contentType = contentType
        self.contentEncoding = contentEncoding
        self.enableCORS = enableCORS
        self.supportMethods = set(methods)
        self.supportMethods.add("OPTIONS")

    def __call__(self, func):
        def wrapped_func(*args, **namedArgs):
            return func(*args, **namedArgs)

        wrapped_func.exposed = True
        wrapped_func.contentType = self.contentType
        wrapped_func.contentEncoding = self.contentEncoding
        wrapped_func.enableCORS = self.enableCORS
        wrapped_func.supportMethods = self.supportMethods
        wrapped_func.__doc__ = func.__doc__
        wrapped_func.originalFunction = func 
        return wrapped_func


@expose(contentType='text/html; charset=utf-8')
def global_default():
    return 'Missing Page: %s' % web.ctx.path

def get_default_handler(nodeHandlers):
    for nodeHandler in reversed(nodeHandlers):
        try:
            return getattr(nodeHandler, 'default')
        except AttributeError:
            pass 
                
    return global_default 

def get_index_handler(nodeHandlers):
    try:
        nodeHandler = nodeHandlers[-1]
        return getattr(nodeHandler, 'index')
    except AttributeError:
        return None


class Site:
    pass


def zipIt(content, compresslevel=5):
    out = BytesIO()
    f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=compresslevel)
    f.write(bytes(content, 'utf-8'))
    f.close()
    return out.getvalue()

def unzipIt(content, compresslevel=5):
    out = BytesIO(content)
    f = gzip.GzipFile(fileobj=out, mode='r', compresslevel=compresslevel)
    return f.read()

def parseQuery(query):
    storage = web.Storage()
    query = query.strip()
    if query.startswith('?'):
        query = query[1:]
    
    for parameter in query.split('&'):
        key, *val = parameter.split('=')
        if not key:
            continue 
        if val == []:
            val = True 
        else:
            val = '='.join(val)
            val = unquote(val)

    
        try:
            oldValue = storage[key]
            if isinstance(oldValue, list):
                oldValue.append(val)
            else:
                storage[key] = [oldValue, val]
        except KeyError:
            storage[key] = val
        
    return storage

class Index:
    root = None 

    def getNodeHandler(self, path):
        if callable(self.root):
            nodeHandler = self.root()
        else:
            nodeHandler = self.root 
        nodeHandlers = [nodeHandler]
        if nodeHandler is None:
            nodeHandler = get_default_handler([nodeHandlers])
        else:
            for node in path:
                if not node:
                    break 
                try:
                    nodeHandler = getattr(nodeHandler, node)
                    nodeHandlers.append(nodeHandler)
                    if callable(nodeHandler):
                        exposed = nodeHandler.exposed

                except AttributeError:
                    nodeHandler = get_default_handler(nodeHandlers) 
                    break 


            if not callable(nodeHandler) and isinstance(nodeHandler, Site):
                nodeHandler = get_index_handler(nodeHandlers)
                if not nodeHandler:
                    nodeHandler = get_default_handler(nodeHandlers)
        return nodeHandler 

    def addDefaultHeaders(self, method, nodeHandler):
        methods = ", ".join(nodeHandler.supportMethods)
        if nodeHandler.enableCORS is not None:
            web.header('Access-Control-Allow-Origin', nodeHandler.enableCORS, unique=True)
            web.header('Access-Control-Allow-Methods', methods, unique=True),
            web.header('Access-Control-Allow-Headers', 'Authorization, Content-Type', unique=True)    
        
        if method not in nodeHandler.supportMethods:
            class MethodCheckObject:
                def __getattribute__(self, name: str):
                    if name not in nodeHandler.supportMethods:
                        raise AttributeError() 
                    return None
            raise web.nomethod(cls=MethodCheckObject())
        else:
            web.header('Allow', methods)

    def GET(self):
        path = web.ctx.path.split('/')[1:]
        nodeHandler = self.getNodeHandler(path)

        self.addDefaultHeaders("GET", nodeHandler)
        
        web.header('Content-Type', nodeHandler.contentType)
        if nodeHandler.contentEncoding:
            web.header('Content-Encoding', nodeHandler.contentEncoding)
                
        query = parseQuery(web.ctx.query)
        try:
            result = nodeHandler(**query)
        except TypeError as err:
            #If this is global handler it might have 0 parameters as input
            #If this is a method handler, than it would have one parameter by default as self but we can't 
            #rely on the parameter name. So, a simple short cut is, if there are more than one parameters
            #then we raise the exception further
            functionSignature = signature(nodeHandler.originalFunction)
            if len(functionSignature.parameters) > 1:
                raise (err)
            result = nodeHandler()
        return result 

    def POST(self):
        
        path = web.ctx.path.split('/')[1:]
        nodeHandler = self.getNodeHandler(path)
        
        self.addDefaultHeaders("POST", nodeHandler)

        query = parseQuery(web.ctx.query)
        #
        #TODO: Current method finds the same URL handler as in the GET case, but we do not have a way
        #      to thell the handler that this is a POST request so we pass a keyword argument. It
        #      is up to the handler to handle this argument.
        #
        #      Alternatively we can thinkg of our methods as get_handler() and post_handler(). To support 
        #      the existing implementation we should consider handler() as get_handler() so we can simply 
        #      add post_handler() concept. If the URL is triggerred by POST action we look for post_handler 
        #      instead of handler. But this might create trouble for default handling etc. So perhaps _post 
        #      keyword is the simplest approach
        #
        assert '_post' not in query, '_post is a reserved keyword'
        query['_post'] = True 
        try:
            result = nodeHandler(**query)
        except TypeError as err:
            #If this is global handler it might have 0 parameters as input
            #If this is a method handler, than it would have one parameter by default as self but we can't 
            #rely on the parameter name. So, a simple short cut is, if there are more than one parameters
            #then we raise the exception further
            functionSignature = signature(nodeHandler.originalFunction)
            if len(functionSignature.parameters) > 1:
                raise (err)
            result = nodeHandler()
        return result 

    def OPTIONS(self):
        path = web.ctx.path.split('/')[1:]
        nodeHandler = self.getNodeHandler(path)

        self.addDefaultHeaders("OPTIONS", nodeHandler)
        return ""


class Application(web.application):
    def __init__(self, root=None, urls=None, globals=globals()):
        if urls is None:
            urls = URLS

        Index.root = root 

        web.application.__init__(self, urls, globals)

    def run(self, address, port, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, (address, port))

    def __get_sitemap(self):
        
        sitemap = []
        def traverse(node, path='/'):
            if not isinstance(node, Site):
                return
            
            nodeHandler = get_index_handler([node])
            if nodeHandler:
                sitemap.append({'url': path, 
                                'handler': node.__class__.__name__, 
                                'description': nodeHandler.__doc__ if nodeHandler.__doc__ else ''})
            if not path.endswith('/'):
                path = path + '/'

            for attr in dir(node):
                nodeHandler = getattr(node, attr)
                
                if callable(nodeHandler):
                    try:
                        exposed = nodeHandler.exposed
                        sitemap.append({'url': path + attr, 
                                        'handler': node.__class__.__name__, 
                                        'description': nodeHandler.__doc__ if nodeHandler.__doc__ else ''})
                    except AttributeError:
                        continue 

                else:
                    traverse(nodeHandler, path + attr)
                


        if Index.root:
            traverse(Index.root)

        return sitemap 

    sitemap = property(__get_sitemap) 

URLS = (
    '/.*', 'webapp.Index'
)


def start(address='0.0.0.0', port=8080):
    ''' '''
    APP = Application(URLS, globals())

    APP.run(address, port)
    
