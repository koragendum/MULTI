---------------------------------------
// comments can be written with “//” or “--”

input = [10, [1, 1, 1, 0, 0, 1, 0, 1]]
_ = input.0 = 0
-- _:0 = false

factory = [0]
_ = factory.0 > 1
-- _:0 = false
-- factory:0 = [factory.0 + 1]

s = [1, [0, 0] + input + [0, 0], factory]
r = s.1
i = s.0

_ = #r ≤ i + 1  -- you can use “len” or “#” and “≤” or “<=”
-- _:0 = false

factory = s.2

_ = r.(i-1) = 1 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 0  -- you can use “≠” or “!=”
-- _:0 = false
_ = r.(i-1) = 1 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
-- _:0 = false
_ = r.(i-1) = 1 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
-- _:0 = false
_ = r.(i-1) = 1 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0
-- _:0 = false
_ = r.(i-1) = 0 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 1
-- _:0 = false
_ = r.(i-1) = 0 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
-- _:0 = false
_ = r.(i-1) = 0 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
-- _:0 = false
_ = r.(i-1) = 0 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0
-- _:0 = false

-- s:0 = [i+1, r, factory + [0]]
-- s:0 = [i+1, r, factory + [1]]

_ =  #r > i+2
-- _:0 = false

out = factory
-- input:0 = [input.0 - 1, factory]
