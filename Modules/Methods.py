from opcua import uamethod


@uamethod
def test(parent, ActionName, MethodArguments):
    print("My parent is: ", parent,
          ActionName, MethodArguments)
    return ["2", "OK"]
