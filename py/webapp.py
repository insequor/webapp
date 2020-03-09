# -*- coding: iso-8859-15 -*-
import web

class expose:
    def __init__(self, contentType):
        self.contentType = contentType 

    def __call__(self, func):
        def wrapped_func(*args):
            return func(*args)

        wrapped_func.exposed = True
        wrapped_func.contentType = self.contentType
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
        return get_default_handler(nodeHandlers)

class Index:
    root = None 
    def GET(self):
        path = web.ctx.path.split('/')[1:]
        nodeHandler = self.root 
        nodeHandlers = [nodeHandler]
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


        if not callable(nodeHandler):
            nodeHandler = get_index_handler(nodeHandlers)

        web.header('Content-Type', nodeHandler.contentType)
        
        return nodeHandler()
        
class Application(web.application):
    def run(self, address, port, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, (address, port))



URLS = (
    '/.*', 'Index'
)


def start(address='0.0.0.0', port=8080):
    ''' '''
    APP = Application(URLS, globals())

    APP.run(address, port)
    
