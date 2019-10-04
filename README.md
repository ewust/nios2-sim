# nios2-sim


### Installing
---

`sudo apt install python3 python3-pip python3-bottle`

`sudo pip3 install numpy`


### Running
---

`python3 app.py`
Then visit http://127.0.0.1:8080/nios2

### Architecture
---

Submitted solutions are first assembled (uisng `bin/nios2-elf-as`) and linked (using `bin/nios2-elf-ld` and a simple linker script). The resulting binary is then simulated in the Nios2 Python simulator (`sim.py`). `app.py` provides the web interface with jinja2 templates pulled from `views`.


### Developing
---

Each exercise is taken from the `exercises` dictionary in app.py (TODO: put somewhere more sane). Each exercise has an ID (eid) which is the key in the dictionary (e.g. `list-sum`). This key is used in the URL for the exercise (e.g. /nios2/examples/list-sum).

The values in the exercises dictionary are themselves a dictionary of:
- public: set True if the exercise should be listed in the index
- diff: Difficulty of the problem (e.g. easy, medium, hard)
- title: The name of the exercise
- desc: The HTML description for the exercise.
- code: Initial code to be given.
- checker: A function that will be used to verify the program.

If you add an exercise, you will need to create a new element in the exercises dictionary, and define a custom checker function.

### Checker Functions
---

Checker functions take one argument: a JSON object of the assembled program (produced by `nios2\_as`). The checker function must return a tuple `(success, feedback)`, with `success` set to True if all test cases passed, and False otherwise. `feedback` is a string carrying information on failed test cases / dbug help.

The CPU is simulated using a custom nios2 CPU (sim.py), instantiated by `cpu = Nios2(obj=obj)`. The CPU can be executed to completion, breakpoint, error, or 1000 instructions (whichever occurs first) by `cpu.run\_until\_halted(1000)`.

For multiple test cases, you can reset the cpu with `cpu.reset()`, which will reset the memory to the inital program (provided by the JSON object). If a test case fails, you probably want to provide a reason, and as much info as possible; it can be helpful to print out memory and symbol mapping (see the `get_debug()` function).

### Accessing Simulator state
---

The simulator is designed to be accessible from the outside: registers (`get_reg()`, `set_reg()`) and memory (`loadword()`, `storeword()`) can be read/changed. Additionally, the CPU keeps track of symbols, which can be used to read/write their associated words (`get_symbol_word()` `write_symbol_word()`).

MMIO devices can be simulated: each address can be added to the `cpu.mmios` dictionary, with the MMIO address as the key, and the value a callback function that is called when the address is accessed (e.g. ldwio/stwio). The callback function is given either a value (if it's a store) or None (if it's a load).

If you only want a read/write register at the address, you can create a `Nios2.MMIO\_Reg()` which will have an `access` method that can be given to the dictionary:

```python
leds = Nios2.MMIO_Reg()
cpu.mmios[0xFF200000] = leds.access
```

Then later, the value can be read (`leds.load()`).

