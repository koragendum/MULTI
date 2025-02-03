// comments can be written with “//” or “--”

input = [10, [1, 1, 1, 0, 0, 1, 0, 1]]
_:+1 = input.0 = 0
_ = false

factory = [0]
_:+1 = factory.0 > 1
_ = false
factory:0 = [factory.0 + 1]

s = [1, [0, 0] + input + [0, 0], factory]
r = s.1
i = s.0

_:+1 = #r ≤ i + 1  -- you can use “len” or “#” and “≤” or “<=”
_ = false

factory = s.2

_:+1 = r.(i-1) = 1 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 0  -- you can use “≠” or “!=”
_ = false
_:+1 = r.(i-1) = 1 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
_ = false
_:+1 = r.(i-1) = 1 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
_ = false
_:+1 = r.(i-1) = 1 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0
_ = false
_:+1 = r.(i-1) = 0 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 1
_ = false
_:+1 = r.(i-1) = 0 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
_ = false
_:+1 = r.(i-1) = 0 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
_ = false
_:+1 = r.(i-1) = 0 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0
_ = false

s:0 = [i+1, r, factory + [0]]
s:0 = [i+1, r, factory + [1]]

_:+1 =  #r > i+2
_ = false

out = factory
input:0 = [input.0 - 1, factory]

