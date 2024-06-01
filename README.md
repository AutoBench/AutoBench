# AutoBench

This is the code implementation of paper *AutoBench: Automatic Testbench Generation and Evaluation Using LLMs for HDL Design*, which has been submitted to *6th ACM/IEEE International Symposium on Machine Learning for CAD*. 

This open-sourced project contains the `code implementation` of *AutoBench*, the `dataset` (see json files in `data/HDLBits`, the dataset is extended from HDLBits data) and the `experimental results` (see the following google drive link) referred in paper Section V Experimental results. Due to the large size, the experimental results are uploaded to google drive: https://drive.google.com/drive/folders/1EhG9Ch4vDzMtOsDvoiHthU0OWsZP1xRh?usp=sharing.

## What is AutoBench
AutoBench is the first LLM-based testbench generator for digital circuit design, which requires only the description of the design under test (DUT) to automatically generate comprehensive testbenches. In AutoBench, a hybrid testbench structure and a self-checking system are realized using LLMs. To validate the gen- erated testbenches, we also introduce an automated testbench evaluation framework (Eval0, Eval1, Eval2, Eval2b) to evaluate the quality of generated testbenches from multiple perspectives.

## Setup

### softwares

- Python 3.8 or newer.

- A version of Icarus Verilog that totally support ***IEEE Std 1800-2012***.

(We strongly recommend utilizing the latest versions of Python and Icarus Verilog. This is due to the fact that higher version expressions employed by LLMs may result in compatibility issues or bugs when executed in older software versions.)

### LLM API keys

You must insert your OpenAI/Anthropic API key into `config/key_API.json` before running the project.

### Other Notes

If your cpu is heavily occupied or very inefficient, consider enlarging the value for `timeout` in your config file, otherwise simulation may fail due to too much time spent on simulation and the final performance may decrease.

## Running

This project's config is stored in yaml files under `/config`. You have multiple options to run this project.

### Run by preset configs

We provided 4 demos for a quick start, you can access them via args:

- single task demo for CMB circuits: `python main.py -d cmb`
- single task demo for SEQ circuits: `python main.py -d seq`
- full task demo for all circuits: `python main.py -d 156`
- full task demo for all circuits using baseline (directgen): `python main.py -d baseline`

### Run by customized configures

You can change the config file in `config/custom.yaml` to customized your running. Here are explanations for some settings:

- `-save-pub-prefix/subdir/dir`: the saving path of log and results. The saving path will be `dir` + `subdir` + `prefix`.

- `-gpt-model`: the LLM model called in work. Now it perfectly supports OpenAI's conversational LLM model such as gpt3.5, gpt4, gpt3.5turbo, gpt4turbo, gpt4o. please use the official model name such as *gpt-4-turbo-2024-04-09* in this option. It also imperfectly support Claude3 models. But we do not guarantee that the Claude3 model will function flawlessly in our work.
  
- `-autoline-probset-only`: this is a list letting programm only run tasks in it. For instance, if I only want to run two tasks: *mux2to1v* and *m2014_q4b*, I should write ['mux2to1v', 'm2014_q4b'] here.
  
- `-autoline-timeout`: Verilog or Python codes that runs more than this value will be considered as failed because LLM-generated codes may have a finite loop. If your computer is old or heavily occupied, enlarge this value. If too small, some correct codes may be distiguished as failed; if too large, the generated signal file in the finite loop may be too large to stop your computer.
  
- `-autoline-promptscript`: if you want to run AutoBench, then `pychecker`; If you want to run baseline, then `directgen`

I would not recommend modifying other configuration items unless you possess sufficient understanding of these components.

## Other Notes

- This version of AutoBench is anonymous version for paper review. After paper being accepted, some information such as author will be released.

- During its development phase, Autobench was also referred to by the project names "TaistBench" and "ChatBench".
