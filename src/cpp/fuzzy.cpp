#include <math.h>
#include "fuzzy.h"


float FuzzyVariable::centre(int crispValue, int median, int deviation)
{
	if( crispValue < median )
	{
		int d = median - crispValue;
		if (d >= deviation)
			return 0;
		else
			return 1.0f - (float)d / deviation;
	}
	else if ( crispValue > median )
	{
		int d = crispValue - median;
		if (d >= deviation)
			return 0;
		else
			return 1.0f - (float)d / deviation;
	}
	else
		return 1.0f;
}


float FuzzyVariable::left(int crispValue, int median, int deviation)
{
	if( crispValue <= median )
		return 1.0f;
	else
	{
		return centre(crispValue, median, deviation);
	}
}


float FuzzyVariable::right(int crispValue, int median, int deviation)
{
	if( crispValue >= median )
		return 1.0f;
	else
		return centre(crispValue, median, deviation);
}


float FuzzyVariable::hedge(Hedge hedge, float membership)
{
	float m = membership;

	switch(hedge)
	{
		case A_LITTLE:
			m = pow(membership, 1.3);
			break;

		case SLIGHTLY:
			m = pow(membership, 1.7);
			break;

		case VERY:
			m = pow(membership, 2);
			break;

		case EXTREMELY:
			m = pow(membership, 3);
			break;

		case VERY_VERY:
			m = pow(membership, 4);
			break;

		case SOMEWHAT:
			m = sqrt(membership);
			break;

		case INDEED:
			if (0 <= membership && membership <= 0.5)
				m = 2 * pow(membership, 2);
			else
				m = 1 - 2 * pow((1 - membership), 2);
			break;
	}
	return (float)m;
}

