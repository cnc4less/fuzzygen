#include <stdio.h>
#include "fuzzy_engine.h"

int main(int argc, char *argv[])
{
	obstruction.setCrispValue(200);
	runFuzzyEngine();
	printf("Left = %d, Right = %d\n", left.getCrispValue(), right.getCrispValue());

	obstruction.setCrispValue(100);
	runFuzzyEngine();
	printf("Left = %d, Right = %d\n", left.getCrispValue(), right.getCrispValue());

	obstruction.setCrispValue(50);
	runFuzzyEngine();
	printf("Left = %d, Right = %d\n", left.getCrispValue(), right.getCrispValue());

	return 0;
}
