// comments can be written with “//” or “--”

input = [10, [1, 1, 1, 0, 0, 1, 0, 1]]
_:+1 = input.0 = 0
_ = false

factory = [0]
_:+1 = factory.0 > 1
_ = false
factory:0 = [factory.0 + 1]
