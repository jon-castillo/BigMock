class leveltype(object):
    type_root =          0
    type_normalbracket = 1
    type_namespace     = 2
    type_class         = 3
    type_struct        = 4
    type_method        = 5
    type_enum          = 6
    type_extern        = 7

class Stack:
     def __init__(self):
         self.items = []

     def isEmpty(self):
         return self.items == []

     def push(self, item):
         self.items.append(item)

     def pop(self):
         return self.items.pop()

     def peek(self):
         return self.items[len(self.items)-1]

     def size(self):
         return len(self.items)

     def parent(self):
         x = 1
         while (self.items[len(self.items)-x] == leveltype.type_normalbracket):
             x = x+1
         return self.items[len(self.items)-x]

     def onExit(self):
         #todo
         if parent() == leveltype.type_root:
             return False
         if parent() == leveltype.type_normalbracket:
             return False
         if parent() == leveltype.type_namespace:
             return False
         if parent() == leveltype.type_class:
             return False
         if parent() == leveltype.type_struct:
             return False
         if parent() == leveltype.type_method:
             return False
         if parent() == leveltype.type_enum:
             return False
         if parent() == leveltype.type_extern:
             return False
    
     def onEntry(self):
         #todo
         if parent() == leveltype.type_root:
             return False
         if parent() == leveltype.type_normalbracket:
             return False
         if parent() == leveltype.type_namespace:
             return False
         if parent() == leveltype.type_class:
             return False
         if parent() == leveltype.type_struct:
             return False
         if parent() == leveltype.type_method:
             return False
         if parent() == leveltype.type_enum:
             return False
         if parent() == leveltype.type_extern:
             return False
         
