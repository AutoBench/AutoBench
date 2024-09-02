class GoldenDUT:
    def __init__(self):
        # Initial state set to unknown 'x', let's assume it's 0 for practical purposes.
        self.q_reg = 0

    def load(self, signal_vector):
        # Update internal registers based on the signal vector.
        # This essentially prepares the state for the next clock cycle.
        if signal_vector['ar'] == 1:
            self.q_reg = 0  # Asynchronous reset sets q to 0
        else:
            self.q_reg = signal_vector['d']  # Follow the data input if reset is not active

    def check(self, signal_vector):
        # Determine expected output value 'q' and compare with output signals from DUT.
        expected_q = self.q_reg
        observed_q = signal_vector['q']
        if expected_q != observed_q:
            print(f"Scenario: {signal_vector['scenario']}, expected: q={expected_q}, observed q={observed_q}")
            return False
        return True

def check_dut(vectors_in):
    golden_dut = GoldenDUT()
    failed_scenarios = []
    for vector in vectors_in:
        if vector["check_en"]:
            check_pass = golden_dut.check(vector)
            if check_pass:
                print(f"Passed; vector: {vector}")
            else:
                print(f"Failed; vector: {vector}")
                failed_scenarios.append(vector["scenario"])
        golden_dut.load(vector)
    return failed_scenarios

def SignalTxt_to_dictlist(txt:str):
    signals = []
    lines = txt.strip().split("\n")
    for line in lines:
        signal = {}
        if line.startswith("[check]"):
            signal["check_en"] = True
            line = line[7:]
        elif line.startswith("scenario"):
            signal["check_en"] = False
        else:
            continue
        line = line.strip().split(", ")
        for item in line:
            if "scenario" in item:
                item = item.split(": ")
                signal["scenario"] = item[1].replace(" ", "")
            else:
                item = item.split(" = ")
                key = item[0]
                value = item[1]
                if ("x" not in value) and ("X" not in value) and ("z" not in value):
                    signal[key] = int(value)
                else:
                    if ("x" in value) or ("X" in value):
                        signal[key] = 0 # used to be "x"
                    else:
                        signal[key] = 0 # used to be "z"
        signals.append(signal)
    return signals
with open("TBout.txt", "r") as f:
    txt = f.read()
vectors_in = SignalTxt_to_dictlist(txt)
tb_pass = check_dut(vectors_in)
print(tb_pass)
