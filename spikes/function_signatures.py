
from inspect import signature 

def testFunction(a, b=None):
    pass 

class TestClass:
    def testMethod(me):
        pass 

if __name__ == '__main__':
    #sig = signature(testFunction)
    sig = signature(TestClass.testMethod)
    for key in sig.parameters:
        param = sig.parameters[key]
        print(key, param, dir(param))
        print('   ', param.kind)
    