from costflow import Costflow, Config


conf = Config()
costflow = Costflow(conf)

inputs = [
    'tomorrow "RiverBank Properties" "Paying the rent" 2400 Assets:US:BofA:Checking > 2400  Expenses:Home:Rent',
    "@Verizon 59.61 Assets:US:BofA:Checking > Expenses:Home:Phone",
    "Dinner 180 CNY bofa > rx + ry + food",
    "Dinner | bofa USD 180  | rx -60 | ry -60 | food -60",
]

for s in inputs:
    entry = costflow.parse(s)
    print(f"Input: {s}")
    print(entry.render())
    print()
