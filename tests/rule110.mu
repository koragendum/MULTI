// comments can be written with “//” or “--”

input = [10, [1, 1, 1, 0, 0, 1, 0, 1]]
die if input.0 = 0

factory = [0]
die if factory.0 > 1
factory:0 = [factory.0 + 1]

s = [1, [0, 0] + input + [0, 0], factory]
r = s.1
i = s.0

die if #r ≤ i + 1  -- you can use “len” or “#” and “≤” or “<=”

factory = s.2

die if r.(i-1) = 1 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 0  -- you can use “≠” or “!=”
die if r.(i-1) = 1 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
die if r.(i-1) = 1 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
die if r.(i-1) = 1 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0
die if r.(i-1) = 0 and r.i = 1 and r.(i+1) = 1 and factory.(i-1) ≠ 1
die if r.(i-1) = 0 and r.i = 1 and r.(i+1) = 0 and factory.(i-1) ≠ 1
die if r.(i-1) = 0 and r.i = 0 and r.(i+1) = 1 and factory.(i-1) ≠ 1
die if r.(i-1) = 0 and r.i = 0 and r.(i+1) = 0 and factory.(i-1) ≠ 0

s:0 = [i+1, r, factory + [0]]
s:0 = [i+1, r, factory + [1]]

die if #r > i+2

out = factory
input:0 = [input.0 - 1, factory]
