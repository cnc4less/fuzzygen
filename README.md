A small-footprint fuzzy logic engine for environments with constrained RAM
but enough CPU power to handle simple floating-point math.

1. Write a fuzzy logic specification in a .fzy file
2. Run your .fzy file through fuzzygen.py to generate fuzzy_engine.h, fuzzy_engine.cpp
3. Compile and link with the fuzzy.h, fuzzy.cpp libraries provided

This was originally created for the Arduino platform so it doesn't have a lot
of customization or use of namespaces.
