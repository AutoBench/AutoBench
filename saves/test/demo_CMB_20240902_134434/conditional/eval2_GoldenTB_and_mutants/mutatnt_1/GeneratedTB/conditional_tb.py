def calculate_expected_min(a, b, c, d):
    """
    Calculate the expected minimum value among four 8-bit unsigned integers.
    
    Parameters:
    a (int): Input value a.
    b (int): Input value b.
    c (int): Input value c.
    d (int): Input value d.
    
    Returns:
    int: The smallest value among a, b, c, and d.
    """
    values = [a, b, c, d]
    minimum_value = min(values)
    return minimum_value

def check_dut(test_vectors: list) -> list:
    """
    Check the functional correctness of the DUT based on test vectors provided.
    
    Parameters:
    test_vectors (list): List of dictionaries with each containing scenario description and input-output signals
    
    Returns:
    list: List of indexes of failed scenarios, if all tests pass, returns an empty list
    """
    failed_scenarios = []

    for idx, scenario in enumerate(test_vectors):
        a = scenario['a']
        b = scenario['b']
        c = scenario['c']
        d = scenario['d']
        observed_min = scenario['min']
        
        expected_min = calculate_expected_min(a, b, c, d)
        
        if expected_min != observed_min:
            failed_scenarios.append(scenario['scenario'])

    return failed_scenarios

def SignalTxt_to_dictlist(txt:str):
    lines = txt.strip().split("\n")
    signals = []
    for line in lines:
        signal = {}
        line = line.strip().split(", ")
        for item in line:
            if "scenario" in item:
                item = item.split(": ")
                signal["scenario"] = item[1]
            else:
                item = item.split(" = ")
                key = item[0]
                value = item[1]
                if "x" not in value and "z" not in value:
                    signal[key] = int(value)
                else:
                    signal[key] = value 
        signals.append(signal)
    return signals
with open("TBout.txt", "r") as f:
    txt = f.read()
vectors_in = SignalTxt_to_dictlist(txt)
tb_pass = check_dut(vectors_in)
print(tb_pass)
