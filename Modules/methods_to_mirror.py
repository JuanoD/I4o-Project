from opcua import uamethod
import time


@uamethod
def test(parent, ActionName, MethodArguments):
    print("My parent is: ", parent,
          ActionName, MethodArguments)
    time.sleep(3)
    print("Han pasado tres segundos")
    return ["2", "OK"]
